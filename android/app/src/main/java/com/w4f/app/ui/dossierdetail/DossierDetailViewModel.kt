package com.w4f.app.ui.dossierdetail

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.ReportDetail
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DossierDetailUiState(
  val isLoading: Boolean = true,
  val detail: ReportDetail? = null,
  val douarName: String? = null,
  val error: Boolean = false,
)

/** Section 8, screen 4 — "تفاصيل الملف". Live fetch, not Room-backed (see
 * `ReportRepository.fetchDetail`'s doc comment for why); `error` surfaces a
 * retry affordance rather than silently showing nothing when offline. */
@HiltViewModel
class DossierDetailViewModel
@Inject
constructor(private val reportRepository: ReportRepository, private val douarRepository: DouarRepository) :
  ViewModel() {

  private val _uiState = MutableStateFlow(DossierDetailUiState())
  val uiState: StateFlow<DossierDetailUiState> = _uiState.asStateFlow()

  private var currentReportId: String? = null

  fun load(reportId: String) {
    if (currentReportId == reportId && _uiState.value.detail != null) return
    currentReportId = reportId
    _uiState.update { it.copy(isLoading = true, error = false) }
    viewModelScope.launch {
      reportRepository
        .fetchDetail(reportId)
        .onSuccess { detail ->
          val douarName = douarRepository.getById(detail.douarId)?.nameAr
          _uiState.update { it.copy(isLoading = false, detail = detail, douarName = douarName) }
        }
        .onFailure { _uiState.update { it.copy(isLoading = false, error = true) } }
    }
  }

  fun retry() {
    val reportId = currentReportId ?: return
    currentReportId = null
    load(reportId)
  }
}
