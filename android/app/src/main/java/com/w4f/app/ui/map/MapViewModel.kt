package com.w4f.app.ui.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.Report
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Section 8, screen 6 (الخريطة): a douar's marker color reflects the most
 * recently collected report *this moqaddem* filed there — `/sync/pull` only
 * ever returns the signed-in moqaddem's own reports (section 5), so this is
 * genuinely "my douars", not every report in the territory. Mirrors the
 * web dashboard's own "most recent report per douar" convention
 * (`backend/app/services/dashboard.py`'s `reports_by_douar`). */
enum class DouarMapStatus {
  NO_REPORTS,
  PENDING_SYNC,
  AWAITING_REVIEW,
  HIGH_PRIORITY,
  VALIDATED,
  PROJECT_UNDERWAY,
  REJECTED,
}

data class DouarMarker(val douar: Douar, val status: DouarMapStatus, val score: Int?)

data class MapUiState(val markers: List<DouarMarker> = emptyList())

// Mirrors the backend's own `_PRIORITY_DOUAR_THRESHOLD` in
// `backend/app/services/dashboard.py` — same cutoff, same meaning, kept in
// sync manually since the two codebases don't share constants.
private const val HIGH_PRIORITY_SCORE_THRESHOLD = 70

@HiltViewModel
class MapViewModel
@Inject
constructor(private val douarRepository: DouarRepository, private val reportRepository: ReportRepository) :
  ViewModel() {

  private val _uiState = MutableStateFlow(MapUiState())
  val uiState: StateFlow<MapUiState> = _uiState.asStateFlow()

  init {
    viewModelScope.launch {
      combine(douarRepository.observeAll(), reportRepository.observeReports()) { douars, reports ->
          buildMarkers(douars, reports)
        }
        .collect { markers -> _uiState.update { it.copy(markers = markers) } }
    }
  }
}

/** Visible for testing: pure, no Android/MapLibre dependency so this stays
 * unit-testable even though the screen that renders it (AndroidView +
 * MapLibre's native-backed MapView) isn't — exercised on-device instead,
 * same split already used for CameraX in `EvidenceStep`. */
fun buildMarkers(douars: List<Douar>, reports: List<Report>): List<DouarMarker> {
  val latestReportByDouar = reports.groupBy { it.douarId }.mapValues { (_, rs) -> rs.maxBy { it.collectedAt } }
  return douars
    .filter { it.lat != null && it.lon != null }
    .map { douar ->
      val report = latestReportByDouar[douar.id]
      DouarMarker(douar, classify(report), report?.serverScore)
    }
}

private fun classify(report: Report?): DouarMapStatus {
  if (report == null) return DouarMapStatus.NO_REPORTS
  val status = report.serverStatus ?: return DouarMapStatus.PENDING_SYNC
  return when (status) {
    "converted_to_project" -> DouarMapStatus.PROJECT_UNDERWAY
    "rejected" -> DouarMapStatus.REJECTED
    "validated" ->
      if ((report.serverScore ?: 0) >= HIGH_PRIORITY_SCORE_THRESHOLD) {
        DouarMapStatus.HIGH_PRIORITY
      } else {
        DouarMapStatus.VALIDATED
      }
    // submitted / under_review / recheck_requested.
    else -> DouarMapStatus.AWAITING_REVIEW
  }
}
