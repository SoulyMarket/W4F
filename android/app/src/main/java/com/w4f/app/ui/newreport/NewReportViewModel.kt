package com.w4f.app.ui.newreport

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.location.CapturedLocation
import com.w4f.app.data.location.LocationClient
import com.w4f.app.data.media.MediaCompressor
import com.w4f.app.data.media.MediaFileStore
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.MediaKind
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportMedia
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.SyncState
import com.w4f.app.domain.model.WaterSource
import com.w4f.app.sync.SyncScheduler
import dagger.hilt.android.lifecycle.HiltViewModel
import java.io.File
import java.time.Instant
import java.time.LocalDate
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

const val NEW_REPORT_FIRST_STEP = 1
const val NEW_REPORT_LAST_STEP = 5

data class CapturedMediaDraft(
  val id: String,
  val kind: MediaKind,
  val localUri: String,
  val mimeType: String,
  val sizeBytes: Long,
  val capturedAt: Instant,
)

data class NewReportUiState(
  val step: Int = NEW_REPORT_FIRST_STEP,
  // Step 1 — الدوار
  val douarQuery: String = "",
  val douarResults: List<Douar> = emptyList(),
  val selectedDouar: Douar? = null,
  // Step 2 — المشكل
  val waterSource: WaterSource? = null,
  val problemType: ProblemType? = null,
  val interruptionFrequency: InterruptionFrequency? = null,
  val severityReported: SeverityLevel? = null,
  val waterQualityRisk: Boolean = false,
  // Step 3 — الأرقام
  val affectedFamilies: String = "",
  val affectedPeople: String = "",
  val durationDays: String = "",
  val hasAlternativeSource: Boolean = false,
  val alternativeDistanceKm: String = "",
  // Step 4 — الإثباتات
  val media: List<CapturedMediaDraft> = emptyList(),
  val location: CapturedLocation? = null,
  val isCapturingLocation: Boolean = false,
  // Step 5 — ملخص
  val isSaving: Boolean = false,
  val savedReportId: String? = null,
) {
  val isDouarStepValid: Boolean
    get() = selectedDouar != null

  val isProblemStepValid: Boolean
    get() =
      waterSource != null &&
        problemType != null &&
        interruptionFrequency != null &&
        severityReported != null

  val isNumbersStepValid: Boolean
    get() =
      affectedFamilies.toIntOrNull() != null &&
        affectedPeople.toIntOrNull() != null &&
        durationDays.toIntOrNull() != null &&
        (!hasAlternativeSource || alternativeDistanceKm.toDoubleOrNull() != null)

  val canGoNext: Boolean
    get() =
      when (step) {
        1 -> isDouarStepValid
        2 -> isProblemStepValid
        3 -> isNumbersStepValid
        // Evidence (step 4) is never required to advance — section 8: never
        // block data entry on media or GPS.
        else -> true
      }

  val isReadyToSave: Boolean
    get() = isDouarStepValid && isProblemStepValid && isNumbersStepValid
}

@HiltViewModel
class NewReportViewModel
@Inject
constructor(
  private val douarRepository: DouarRepository,
  private val reportRepository: ReportRepository,
  private val locationClient: LocationClient,
  private val mediaFileStore: MediaFileStore,
  private val syncScheduler: SyncScheduler,
) : ViewModel() {

  private val _uiState = MutableStateFlow(NewReportUiState())
  val uiState: StateFlow<NewReportUiState> = _uiState.asStateFlow()

  private var douarSearchJob: Job? = null

  init {
    runDouarSearch("")
  }

  fun onDouarQueryChange(query: String) {
    _uiState.update { it.copy(douarQuery = query) }
    runDouarSearch(query)
  }

  private fun runDouarSearch(query: String) {
    douarSearchJob?.cancel()
    douarSearchJob =
      viewModelScope.launch {
        douarRepository.search(query).collect { results ->
          _uiState.update { it.copy(douarResults = results) }
        }
      }
  }

  fun onDouarSelected(douar: Douar) {
    _uiState.update { it.copy(selectedDouar = douar) }
  }

  fun onWaterSourceSelected(value: WaterSource) {
    _uiState.update { it.copy(waterSource = value) }
  }

  fun onProblemTypeSelected(value: ProblemType) {
    _uiState.update { it.copy(problemType = value) }
  }

  fun onInterruptionFrequencySelected(value: InterruptionFrequency) {
    _uiState.update { it.copy(interruptionFrequency = value) }
  }

  fun onSeveritySelected(value: SeverityLevel) {
    _uiState.update { it.copy(severityReported = value) }
  }

  fun onWaterQualityRiskToggle(value: Boolean) {
    _uiState.update { it.copy(waterQualityRisk = value) }
  }

  fun onAffectedFamiliesChange(value: String) {
    if (value.isEmpty() || value.toIntOrNull() != null) _uiState.update { it.copy(affectedFamilies = value) }
  }

  fun onAffectedPeopleChange(value: String) {
    if (value.isEmpty() || value.toIntOrNull() != null) _uiState.update { it.copy(affectedPeople = value) }
  }

  fun onDurationDaysChange(value: String) {
    if (value.isEmpty() || value.toIntOrNull() != null) _uiState.update { it.copy(durationDays = value) }
  }

  fun onHasAlternativeSourceToggle(value: Boolean) {
    _uiState.update { it.copy(hasAlternativeSource = value) }
  }

  fun onAlternativeDistanceChange(value: String) {
    if (value.isEmpty() || value.toDoubleOrNull() != null) {
      _uiState.update { it.copy(alternativeDistanceKm = value) }
    }
  }

  fun captureLocation() {
    _uiState.update { it.copy(isCapturingLocation = true) }
    viewModelScope.launch {
      val location = locationClient.getCurrentLocation()
      _uiState.update { it.copy(location = location, isCapturingLocation = false) }
    }
  }

  /** CameraX's output target for a raw photo capture — compressed and
   * moved into permanent storage once the capture actually completes. */
  fun newRawPhotoCaptureFile(): File = mediaFileStore.newRawPhotoCaptureFile()

  fun newVideoFile(): File = mediaFileStore.newVideoFile()

  /** Section 8: "compress photos (max 1600 px long side, JPEG ~80%)" —
   * runs off the main thread since decoding/re-encoding a full-resolution
   * photo is real CPU work. */
  fun onPhotoCaptured(rawFile: File) {
    viewModelScope.launch {
      val compressed = withContext(Dispatchers.Default) { MediaCompressor.compressJpegFile(rawFile) }
      val finalFile = mediaFileStore.newPhotoFile().apply { writeBytes(compressed) }
      rawFile.delete()
      addMedia(MediaKind.PHOTO, finalFile.absolutePath, "image/jpeg", finalFile.length())
    }
  }

  fun onVideoCaptured(file: File) {
    addMedia(MediaKind.VIDEO, file.absolutePath, "video/mp4", file.length())
  }

  private fun addMedia(kind: MediaKind, localUri: String, mimeType: String, sizeBytes: Long) {
    val draft =
      CapturedMediaDraft(
        id = UUID.randomUUID().toString(),
        kind = kind,
        localUri = localUri,
        mimeType = mimeType,
        sizeBytes = sizeBytes,
        capturedAt = Instant.now(),
      )
    _uiState.update { it.copy(media = it.media + draft) }
  }

  fun onRemoveMedia(id: String) {
    _uiState.update { it.copy(media = it.media.filterNot { draft -> draft.id == id }) }
  }

  fun onNextStep() {
    val state = _uiState.value
    if (!state.canGoNext || state.step >= NEW_REPORT_LAST_STEP) return
    _uiState.update { it.copy(step = it.step + 1) }
  }

  fun onPreviousStep() {
    _uiState.update { it.copy(step = (it.step - 1).coerceAtLeast(NEW_REPORT_FIRST_STEP)) }
  }

  fun onConfirmSave() {
    val state = _uiState.value
    if (!state.isReadyToSave) return
    val douar = state.selectedDouar ?: return
    val waterSource = state.waterSource ?: return
    val problemType = state.problemType ?: return
    val interruptionFrequency = state.interruptionFrequency ?: return
    val severityReported = state.severityReported ?: return
    val durationDays = state.durationDays.toIntOrNull() ?: return

    _uiState.update { it.copy(isSaving = true) }
    viewModelScope.launch {
      val reportId = UUID.randomUUID().toString()
      val now = Instant.now()
      val report =
        Report(
          id = reportId,
          douarId = douar.id,
          waterSource = waterSource,
          problemType = problemType,
          // Section 8's "الأرقام" step only collects duration, not a
          // separate start-date picker — derived here rather than adding a
          // field the screen spec doesn't list.
          problemStartedOn = LocalDate.now().minusDays(durationDays.toLong()),
          durationDays = durationDays,
          interruptionFrequency = interruptionFrequency,
          hasAlternativeSource = state.hasAlternativeSource,
          alternativeDistanceKm = if (state.hasAlternativeSource) state.alternativeDistanceKm.toDoubleOrNull() else null,
          severityReported = severityReported,
          waterQualityRisk = state.waterQualityRisk,
          affectedFamilies = state.affectedFamilies.toIntOrNull() ?: 0,
          affectedPeople = state.affectedPeople.toIntOrNull() ?: 0,
          observations = null,
          lat = state.location?.lat,
          lon = state.location?.lon,
          locationAccuracyM = state.location?.accuracyM,
          collectedAt = now,
          syncState = SyncState.PENDING,
          syncError = null,
          serverStatus = null,
          serverScore = null,
        )
      val media =
        state.media.map { draft ->
          ReportMedia(
            id = draft.id,
            reportId = reportId,
            kind = draft.kind,
            localUri = draft.localUri,
            mimeType = draft.mimeType,
            sizeBytes = draft.sizeBytes,
            capturedAt = draft.capturedAt,
            syncState = SyncState.PENDING,
          )
        }
      reportRepository.saveNewReport(report, media)
      _uiState.update { it.copy(isSaving = false, savedReportId = reportId) }
      syncScheduler.syncNow()
    }
  }
}
