package com.w4f.app.ui.map

import android.graphics.Color as AndroidColor
import android.graphics.PointF
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.w4f.app.R
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.Style
import org.maplibre.android.offline.OfflineManager
import org.maplibre.android.offline.OfflineRegion
import org.maplibre.android.offline.OfflineRegionError
import org.maplibre.android.offline.OfflineRegionStatus
import org.maplibre.android.offline.OfflineTilePyramidRegionDefinition
import org.maplibre.android.style.expressions.Expression
import org.maplibre.android.style.layers.CircleLayer
import org.maplibre.android.style.layers.PropertyFactory
import org.maplibre.android.style.sources.GeoJsonSource
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.Point

// A free, no-API-key-required public MapLibre demo style (vector tiles) —
// appropriate for this prototype since the project has no tile-hosting
// contract of its own (section 8 only specifies "offline tiles for my
// territory", not which base style to render them from).
private const val BASE_STYLE_URL = "https://demotiles.maplibre.org/style.json"
private const val SOURCE_ID = "w4f-douars"
private const val LAYER_ID = "w4f-douars-circles"
private const val PROPERTY_ID = "id"
private const val PROPERTY_STATUS = "status"

/** Section 8, screen 6 (الخريطة). Markers come from [MapViewModel] (pure,
 * unit-tested status classification); everything MapLibre-specific —
 * rendering, tap-to-inspect, offline tile download — lives here and is
 * verified on-device instead, the same split already used for CameraX in
 * `EvidenceStep` (native-backed APIs that Robolectric can't exercise). */
@Composable
fun MapScreen(modifier: Modifier = Modifier, viewModel: MapViewModel = hiltViewModel()) {
  val uiState by viewModel.uiState.collectAsState()
  val context = LocalContext.current
  var selectedMarker by remember { mutableStateOf<DouarMarker?>(null) }
  var offlineState by remember { mutableStateOf(OfflineDownloadUiState()) }

  // Reflects a region downloaded in a previous session — without this the
  // button would always claim "not downloaded yet" even right after
  // reopening the app on an already-cached territory.
  LaunchedEffect(Unit) {
    OfflineManager.getInstance(context)
      .listOfflineRegions(
        object : OfflineManager.ListOfflineRegionsCallback {
          override fun onList(offlineRegions: Array<OfflineRegion>?) {
            if (!offlineRegions.isNullOrEmpty()) {
              offlineState = offlineState.copy(isAvailableOffline = true)
            }
          }

          override fun onError(error: String) = Unit
        }
      )
  }

  Column(modifier = modifier.fillMaxSize()) {
    Text(
      text = stringResource(R.string.map_title),
      style = MaterialTheme.typography.titleLarge,
      modifier = Modifier.padding(bottom = 8.dp),
    )

    Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
      MapLibreMapView(
        markers = uiState.markers,
        onMarkerClick = { selectedMarker = it },
        modifier = Modifier.fillMaxSize(),
      )
    }

    MapLegend(modifier = Modifier.padding(vertical = 8.dp))

    selectedMarker?.let { marker ->
      MarkerInfoCard(marker = marker, onDismiss = { selectedMarker = null })
    }

    OfflineDownloadBar(
      state = offlineState,
      enabled = uiState.markers.isNotEmpty() && !offlineState.isDownloading,
      onDownloadClick = {
        val bounds = boundingBoxOf(uiState.markers)
        if (bounds != null) {
          offlineState = offlineState.copy(isDownloading = true, progressFraction = null, error = null)
          downloadOfflineRegion(context, bounds) { update -> offlineState = update }
        }
      },
      modifier = Modifier.padding(top = 8.dp),
    )
  }
}

@Composable
private fun MapLibreMapView(
  markers: List<DouarMarker>,
  onMarkerClick: (DouarMarker) -> Unit,
  modifier: Modifier = Modifier,
) {
  val context = LocalContext.current
  val lifecycleOwner = LocalLifecycleOwner.current
  val currentMarkers = rememberUpdatedState(markers)
  val currentOnMarkerClick = rememberUpdatedState(onMarkerClick)

  // Deliberately NOT called from W4FApplication.onCreate(): that runs under
  // Robolectric too (every Context-based unit test instantiates the real
  // Application), and this loads a native library Robolectric's JVM
  // doesn't have — confirmed by 13 unrelated DAO/compressor tests failing
  // with UnsatisfiedLinkError until the call was moved here, where it only
  // ever runs on a real device screen.
  val mapView =
    remember {
      MapLibre.getInstance(context)
      MapView(context).apply { onCreate(null) }
    }
  var style by remember { mutableStateOf<Style?>(null) }
  var mapLibreMap by remember { mutableStateOf<MapLibreMap?>(null) }

  DisposableEffect(lifecycleOwner, mapView) {
    val observer =
      LifecycleEventObserver { _, event ->
        when (event) {
          Lifecycle.Event.ON_START -> mapView.onStart()
          Lifecycle.Event.ON_RESUME -> mapView.onResume()
          Lifecycle.Event.ON_PAUSE -> mapView.onPause()
          Lifecycle.Event.ON_STOP -> mapView.onStop()
          Lifecycle.Event.ON_DESTROY -> mapView.onDestroy()
          else -> Unit
        }
      }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
  }

  LaunchedEffect(mapView) {
    mapView.getMapAsync { map ->
      mapLibreMap = map
      map.setStyle(Style.Builder().fromUri(BASE_STYLE_URL)) { loadedStyle ->
        val source = GeoJsonSource(SOURCE_ID, buildFeatureCollection(currentMarkers.value))
        loadedStyle.addSource(source)
        loadedStyle.addLayer(buildCircleLayer())
        style = loadedStyle

        boundingBoxOf(currentMarkers.value)?.let { bounds ->
          map.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds, 64))
        }
      }
      map.addOnMapClickListener { latLng ->
        val point = map.projection.toScreenLocation(latLng)
        val feature =
          map.queryRenderedFeatures(PointF(point.x, point.y), LAYER_ID).firstOrNull()
        val id = feature?.getStringProperty(PROPERTY_ID)
        val marker = currentMarkers.value.firstOrNull { it.douar.id == id }
        if (marker != null) {
          currentOnMarkerClick.value(marker)
          true
        } else {
          false
        }
      }
    }
  }

  LaunchedEffect(markers, style) {
    style?.getSourceAs<GeoJsonSource>(SOURCE_ID)?.setGeoJson(buildFeatureCollection(markers))
  }

  AndroidView(factory = { mapView }, modifier = modifier)
}

private fun buildFeatureCollection(markers: List<DouarMarker>): FeatureCollection {
  val features =
    markers.map { marker ->
      val point = Point.fromLngLat(marker.douar.lon!!, marker.douar.lat!!)
      Feature.fromGeometry(point).apply {
        addStringProperty(PROPERTY_ID, marker.douar.id)
        addStringProperty(PROPERTY_STATUS, marker.status.name)
      }
    }
  return FeatureCollection.fromFeatures(features)
}

private fun buildCircleLayer(): CircleLayer =
  CircleLayer(LAYER_ID, SOURCE_ID)
    .withProperties(
      PropertyFactory.circleRadius(8f),
      PropertyFactory.circleStrokeWidth(2f),
      PropertyFactory.circleStrokeColor(AndroidColor.WHITE),
      PropertyFactory.circleColor(statusColorExpression()),
    )

private fun statusColorExpression(): Expression =
  Expression.switchCase(
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.HIGH_PRIORITY.name)),
    Expression.color(AndroidColor.parseColor("#F44336")),
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.PROJECT_UNDERWAY.name)),
    Expression.color(AndroidColor.parseColor("#4CAF50")),
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.VALIDATED.name)),
    Expression.color(AndroidColor.parseColor("#FFC107")),
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.AWAITING_REVIEW.name)),
    Expression.color(AndroidColor.parseColor("#FF9800")),
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.PENDING_SYNC.name)),
    Expression.color(AndroidColor.parseColor("#2196F3")),
    Expression.eq(Expression.get(PROPERTY_STATUS), Expression.literal(DouarMapStatus.REJECTED.name)),
    Expression.color(AndroidColor.parseColor("#616161")),
    // Default: NO_REPORTS.
    Expression.color(AndroidColor.parseColor("#9E9E9E")),
  )

// Padded so a single douar (or a tight cluster) still downloads a usable
// area around it rather than a near-zero-size tile region.
private const val BOUNDS_PADDING_DEGREES = 0.03

private fun boundingBoxOf(markers: List<DouarMarker>): LatLngBounds? {
  if (markers.isEmpty()) return null
  val builder = LatLngBounds.Builder()
  markers.forEach { builder.include(LatLng(it.douar.lat!!, it.douar.lon!!)) }
  val bounds = builder.build()
  return LatLngBounds.from(
    bounds.getLatNorth() + BOUNDS_PADDING_DEGREES,
    bounds.getLonEast() + BOUNDS_PADDING_DEGREES,
    bounds.getLatSouth() - BOUNDS_PADDING_DEGREES,
    bounds.getLonWest() - BOUNDS_PADDING_DEGREES,
  )
}

private data class OfflineDownloadUiState(
  val isDownloading: Boolean = false,
  val progressFraction: Float? = null,
  val isAvailableOffline: Boolean = false,
  val error: String? = null,
)

private fun downloadOfflineRegion(
  context: android.content.Context,
  bounds: LatLngBounds,
  onUpdate: (OfflineDownloadUiState) -> Unit,
) {
  val definition =
    OfflineTilePyramidRegionDefinition(
      styleURL = BASE_STYLE_URL,
      bounds = bounds,
      minZoom = 0.0,
      maxZoom = 14.0,
      pixelRatio = context.resources.displayMetrics.density,
    )
  val metadata = "w4f-territory".toByteArray()

  OfflineManager.getInstance(context)
    .createOfflineRegion(
      definition,
      metadata,
      object : OfflineManager.CreateOfflineRegionCallback {
        override fun onCreate(offlineRegion: OfflineRegion) {
          offlineRegion.setObserver(
            object : OfflineRegion.OfflineRegionObserver {
              override fun onStatusChanged(status: OfflineRegionStatus) {
                val fraction =
                  if (status.requiredResourceCount > 0) {
                    status.completedResourceCount.toFloat() / status.requiredResourceCount.toFloat()
                  } else {
                    null
                  }
                onUpdate(
                  OfflineDownloadUiState(
                    isDownloading = !status.isComplete,
                    progressFraction = fraction,
                    isAvailableOffline = status.isComplete,
                  )
                )
              }

              override fun onError(error: OfflineRegionError) {
                onUpdate(OfflineDownloadUiState(error = error.message))
              }

              override fun mapboxTileCountLimitExceeded(limit: Long) {
                onUpdate(OfflineDownloadUiState(error = "tile count limit exceeded"))
              }
            }
          )
          offlineRegion.setDownloadState(OfflineRegion.STATE_ACTIVE)
        }

        override fun onError(error: String) {
          onUpdate(OfflineDownloadUiState(error = error))
        }
      },
    )
}

@Composable
private fun OfflineDownloadBar(
  state: OfflineDownloadUiState,
  enabled: Boolean,
  onDownloadClick: () -> Unit,
  modifier: Modifier = Modifier,
) {
  Surface(color = MaterialTheme.colorScheme.surfaceVariant, modifier = modifier.fillMaxWidth()) {
    Column(modifier = Modifier.fillMaxWidth().padding(12.dp)) {
      Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        val label =
          when {
            state.isDownloading -> stringResource(R.string.map_downloading)
            state.isAvailableOffline -> stringResource(R.string.map_download_complete)
            state.error != null -> stringResource(R.string.map_download_error)
            else -> stringResource(R.string.map_download_hint)
          }
        Text(text = label, modifier = Modifier.weight(1f))
        if (state.isDownloading) {
          CircularProgressIndicator(modifier = Modifier.size(20.dp))
        } else {
          Button(onClick = onDownloadClick, enabled = enabled) {
            Text(stringResource(R.string.map_download_offline))
          }
        }
      }
      if (state.isDownloading) {
        val fraction = state.progressFraction
        if (fraction != null) {
          LinearProgressIndicator(progress = { fraction }, modifier = Modifier.fillMaxWidth().padding(top = 8.dp))
        } else {
          LinearProgressIndicator(modifier = Modifier.fillMaxWidth().padding(top = 8.dp))
        }
      }
    }
  }
}

@Composable
private fun MapLegend(modifier: Modifier = Modifier) {
  val entries =
    listOf(
      Color(0xFF9E9E9E) to R.string.map_status_no_reports,
      Color(0xFF2196F3) to R.string.map_status_pending_sync,
      Color(0xFFFF9800) to R.string.map_status_awaiting_review,
      Color(0xFFFFC107) to R.string.map_status_validated,
      Color(0xFFF44336) to R.string.map_status_high_priority,
      Color(0xFF4CAF50) to R.string.map_status_project_underway,
      Color(0xFF616161) to R.string.map_status_rejected,
    )
  LazyRow(modifier = modifier.fillMaxWidth()) {
    items(entries) { (color, labelRes) ->
      Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(end = 16.dp),
      ) {
        Box(modifier = Modifier.size(12.dp).background(color, CircleShape))
        Text(
          text = stringResource(labelRes),
          style = MaterialTheme.typography.labelSmall,
          modifier = Modifier.padding(start = 4.dp),
        )
      }
    }
  }
}

@Composable
private fun MarkerInfoCard(marker: DouarMarker, onDismiss: () -> Unit) {
  Card(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
    Column(modifier = Modifier.padding(12.dp)) {
      Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        Text(text = marker.douar.nameAr, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
        TextButton(onClick = onDismiss) { Text("✕") }
      }
      Text(text = stringResource(marker.status.labelRes()))
      marker.score?.let { score -> Text(text = stringResource(R.string.map_marker_score, score)) }
    }
  }
}

private fun DouarMapStatus.labelRes(): Int =
  when (this) {
    DouarMapStatus.NO_REPORTS -> R.string.map_status_no_reports
    DouarMapStatus.PENDING_SYNC -> R.string.map_status_pending_sync
    DouarMapStatus.AWAITING_REVIEW -> R.string.map_status_awaiting_review
    DouarMapStatus.VALIDATED -> R.string.map_status_validated
    DouarMapStatus.HIGH_PRIORITY -> R.string.map_status_high_priority
    DouarMapStatus.PROJECT_UNDERWAY -> R.string.map_status_project_underway
    DouarMapStatus.REJECTED -> R.string.map_status_rejected
  }
