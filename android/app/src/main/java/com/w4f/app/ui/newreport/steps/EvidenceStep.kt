package com.w4f.app.ui.newreport.steps

import android.Manifest.permission.CAMERA
import android.content.pm.PackageManager
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.FileOutputOptions
import androidx.camera.video.Quality
import androidx.camera.video.QualitySelector
import androidx.camera.video.Recorder
import androidx.camera.video.Recording
import androidx.camera.video.VideoCapture
import androidx.camera.video.VideoRecordEvent
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.w4f.app.R
import com.w4f.app.data.location.CapturedLocation
import com.w4f.app.domain.model.MediaKind
import com.w4f.app.ui.newreport.CapturedMediaDraft
import java.io.File
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Section 8, step 4 — "الإثباتات": photo/video via CameraX, GPS
 * auto-captured with its accuracy shown. Capturing media or a location fix
 * is never required to move on (section 8's offline-first rule: never
 * block data entry on network or GPS). */
@Composable
fun EvidenceStep(
  media: List<CapturedMediaDraft>,
  location: CapturedLocation?,
  isCapturingLocation: Boolean,
  newRawPhotoCaptureFile: () -> File,
  newVideoFile: () -> File,
  onPhotoCaptured: (File) -> Unit,
  onVideoCaptured: (File) -> Unit,
  onRemoveMedia: (String) -> Unit,
  onCaptureLocation: () -> Unit,
) {
  val context = LocalContext.current
  var hasCameraPermission by
    remember {
      mutableStateOf(
        ContextCompat.checkSelfPermission(context, CAMERA) == PackageManager.PERMISSION_GRANTED
      )
    }
  val permissionLauncher =
    androidx.activity.compose.rememberLauncherForActivityResult(
      androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { granted ->
      hasCameraPermission = granted
    }

  LaunchedEffect(Unit) {
    if (location == null && !isCapturingLocation) onCaptureLocation()
  }

  Column(modifier = Modifier.fillMaxWidth()) {
    Text(text = stringResource(R.string.new_report_step4_title), style = MaterialTheme.typography.titleMedium)

    LocationStatus(location = location, isCapturing = isCapturingLocation)

    if (hasCameraPermission) {
      CameraSection(
        newRawPhotoCaptureFile = newRawPhotoCaptureFile,
        newVideoFile = newVideoFile,
        onPhotoCaptured = onPhotoCaptured,
        onVideoCaptured = onVideoCaptured,
      )
    } else {
      Column(modifier = Modifier.padding(top = 16.dp)) {
        Text(stringResource(R.string.new_report_camera_permission_rationale))
        Button(
          onClick = { permissionLauncher.launch(CAMERA) },
          modifier = Modifier.padding(top = 8.dp),
        ) {
          Text(stringResource(R.string.new_report_grant_permission))
        }
      }
    }

    if (media.isNotEmpty()) {
      LazyRow(modifier = Modifier.padding(top = 16.dp)) {
        items(media, key = { it.id }) { item -> MediaThumbnail(item = item, onRemove = { onRemoveMedia(item.id) }) }
      }
    }
  }
}

@Composable
private fun LocationStatus(location: CapturedLocation?, isCapturing: Boolean) {
  Row(
    verticalAlignment = Alignment.CenterVertically,
    modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
  ) {
    when {
      isCapturing -> {
        CircularProgressIndicator(modifier = Modifier.size(20.dp).padding(end = 8.dp))
        Text(stringResource(R.string.new_report_capture_location))
      }
      location != null ->
        Text(stringResource(R.string.new_report_location_captured, location.accuracyM))
      else -> Text(stringResource(R.string.new_report_location_unavailable))
    }
  }
}

@Composable
private fun MediaThumbnail(item: CapturedMediaDraft, onRemove: () -> Unit) {
  Card(modifier = Modifier.padding(end = 8.dp).size(96.dp)) {
    Column {
      Text(
        text = if (item.kind == MediaKind.PHOTO) "📷" else "🎥",
        modifier = Modifier.padding(8.dp),
      )
      IconButton(onClick = onRemove) {
        Text(text = "✕", style = MaterialTheme.typography.labelLarge)
      }
    }
  }
}

private enum class CaptureMode {
  PHOTO,
  VIDEO,
}

@Composable
private fun CameraSection(
  newRawPhotoCaptureFile: () -> File,
  newVideoFile: () -> File,
  onPhotoCaptured: (File) -> Unit,
  onVideoCaptured: (File) -> Unit,
) {
  val context = LocalContext.current
  val lifecycleOwner = LocalLifecycleOwner.current
  val coroutineScope = rememberCoroutineScope()
  val previewView = remember { PreviewView(context) }

  var mode by remember { mutableStateOf(CaptureMode.PHOTO) }
  var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
  var videoCapture by remember { mutableStateOf<VideoCapture<Recorder>?>(null) }
  var activeRecording by remember { mutableStateOf<Recording?>(null) }
  var isRecording by remember { mutableStateOf(false) }
  var recordedSeconds by remember { mutableStateOf(0) }

  DisposableEffect(mode, lifecycleOwner) {
    val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
    val listener = Runnable {
      val cameraProvider = cameraProviderFuture.get()
      val preview = Preview.Builder().build().also { it.surfaceProvider = previewView.surfaceProvider }
      cameraProvider.unbindAll()

      if (mode == CaptureMode.PHOTO) {
        val capture = ImageCapture.Builder().build()
        imageCapture = capture
        videoCapture = null
        cameraProvider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, capture)
      } else {
        val recorder =
          Recorder.Builder().setQualitySelector(QualitySelector.from(Quality.SD)).build()
        val capture = VideoCapture.withOutput(recorder)
        videoCapture = capture
        imageCapture = null
        cameraProvider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, capture)
      }
    }
    cameraProviderFuture.addListener(listener, ContextCompat.getMainExecutor(context))
    onDispose { runCatching { cameraProviderFuture.get().unbindAll() } }
  }

  AndroidView(
    factory = { previewView },
    modifier = Modifier.fillMaxWidth().height(260.dp).padding(top = 12.dp),
  )

  Row(
    horizontalArrangement = Arrangement.spacedBy(8.dp),
    modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
  ) {
    OutlinedButton(onClick = { if (!isRecording) mode = CaptureMode.PHOTO }, enabled = !isRecording) {
      Text(stringResource(R.string.new_report_take_photo))
    }
    OutlinedButton(onClick = { if (!isRecording) mode = CaptureMode.VIDEO }, enabled = !isRecording) {
      Text(stringResource(R.string.new_report_record_video))
    }
  }

  if (mode == CaptureMode.PHOTO) {
    Button(
      onClick = {
        val capture = imageCapture ?: return@Button
        val target = newRawPhotoCaptureFile()
        val outputOptions = ImageCapture.OutputFileOptions.Builder(target).build()
        capture.takePicture(
          outputOptions,
          ContextCompat.getMainExecutor(context),
          object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(output: ImageCapture.OutputFileResults) = onPhotoCaptured(target)

            override fun onError(exception: ImageCaptureException) = Unit
          },
        )
      },
      modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    ) {
      Text(stringResource(R.string.new_report_take_photo))
    }
  } else {
    Button(
      onClick = {
        val capture = videoCapture ?: return@Button
        if (!isRecording) {
          val target = newVideoFile()
          val outputOptions = FileOutputOptions.Builder(target).build()
          activeRecording =
            capture.output
              .prepareRecording(context, outputOptions)
              .start(ContextCompat.getMainExecutor(context)) { event ->
                if (event is VideoRecordEvent.Finalize && !event.hasError()) onVideoCaptured(target)
              }
          isRecording = true
          recordedSeconds = 0
          coroutineScope.launch {
            // Section 8: limit video length (e.g. 60 s).
            while (isRecording && recordedSeconds < MAX_RECORDING_SECONDS) {
              delay(1000)
              recordedSeconds += 1
            }
            if (isRecording) {
              activeRecording?.stop()
              activeRecording = null
              isRecording = false
            }
          }
        } else {
          activeRecording?.stop()
          activeRecording = null
          isRecording = false
        }
      },
      modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    ) {
      Text(stringResource(if (isRecording) R.string.new_report_stop_recording else R.string.new_report_record_video))
    }
  }
}

private const val MAX_RECORDING_SECONDS = 60
