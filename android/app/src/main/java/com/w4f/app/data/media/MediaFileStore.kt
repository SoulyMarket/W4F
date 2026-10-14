package com.w4f.app.data.media

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import java.util.UUID
import javax.inject.Inject

/** App-private storage for captured evidence (section 8) — never shared or
 * external storage, so no runtime storage permission is needed at this
 * minSdk, and nothing here is visible to other apps or the device gallery. */
class MediaFileStore @Inject constructor(@ApplicationContext context: Context) {
  private val mediaDir = File(context.filesDir, "report_media").apply { mkdirs() }
  private val captureTmpDir = File(context.cacheDir, "camera_tmp").apply { mkdirs() }

  /** Where CameraX writes the raw, full-resolution JPEG — short-lived,
   * deleted once [MediaCompressor] produces the final compressed copy. */
  fun newRawPhotoCaptureFile(): File = File(captureTmpDir, "${UUID.randomUUID()}.jpg")

  fun newPhotoFile(): File = File(mediaDir, "${UUID.randomUUID()}.jpg")

  fun newVideoFile(): File = File(mediaDir, "${UUID.randomUUID()}.mp4")
}
