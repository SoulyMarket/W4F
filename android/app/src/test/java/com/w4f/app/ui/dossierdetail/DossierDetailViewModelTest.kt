package com.w4f.app.ui.dossierdetail

import com.w4f.app.data.remote.ApiException
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.ReportDetail
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.WaterSource
import com.w4f.app.testutil.MainDispatcherRule
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class DossierDetailViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val reportRepository: ReportRepository = mock()
  private val douarRepository: DouarRepository = mock()

  private fun viewModel() = DossierDetailViewModel(reportRepository, douarRepository)

  private fun detail(id: String = "r1") =
    ReportDetail(
      id = id,
      douarId = "d1",
      waterSource = WaterSource.WELL,
      problemType = ProblemType.NO_WATER,
      durationDays = 5,
      interruptionFrequency = InterruptionFrequency.DAILY,
      hasAlternativeSource = false,
      alternativeDistanceKm = null,
      severityReported = SeverityLevel.HIGH,
      waterQualityRisk = false,
      affectedFamilies = 3,
      affectedPeople = 12,
      observations = null,
      status = "submitted",
      score = 70,
      media = emptyList(),
      priority = null,
      validations = emptyList(),
      project = null,
    )

  @Test
  fun `load fetches the detail and resolves the douar name`() = runTest {
    whenever(reportRepository.fetchDetail("r1")).thenReturn(Result.success(detail()))
    whenever(douarRepository.getById("d1"))
      .thenReturn(Douar(id = "d1", nameAr = "دوار", nameFr = "Douar", communeId = "c1", lat = null, lon = null))
    val viewModel = viewModel()

    viewModel.load("r1")
    advanceUntilIdle()

    val state = viewModel.uiState.value
    assertFalse(state.isLoading)
    assertFalse(state.error)
    assertEquals("r1", state.detail?.id)
    assertEquals("دوار", state.douarName)
  }

  @Test
  fun `a failed fetch surfaces the error state without a detail`() = runTest {
    whenever(reportRepository.fetchDetail("r1"))
      .thenReturn(Result.failure(ApiException("not_found", "missing")))
    val viewModel = viewModel()

    viewModel.load("r1")
    advanceUntilIdle()

    val state = viewModel.uiState.value
    assertTrue(state.error)
    assertNull(state.detail)
    assertFalse(state.isLoading)
  }

  @Test
  fun `loading the same report twice does not refetch once already loaded`() = runTest {
    whenever(reportRepository.fetchDetail("r1")).thenReturn(Result.success(detail()))
    whenever(douarRepository.getById("d1")).thenReturn(null)
    val viewModel = viewModel()

    viewModel.load("r1")
    advanceUntilIdle()
    viewModel.load("r1")
    advanceUntilIdle()

    verify(reportRepository, org.mockito.kotlin.times(1)).fetchDetail("r1")
  }

  @Test
  fun `retry re-runs the fetch for the current report`() = runTest {
    whenever(reportRepository.fetchDetail("r1"))
      .thenReturn(Result.failure(ApiException("network", "down")))
      .thenReturn(Result.success(detail()))
    whenever(douarRepository.getById("d1")).thenReturn(null)
    val viewModel = viewModel()
    viewModel.load("r1")
    advanceUntilIdle()
    assertTrue(viewModel.uiState.value.error)

    viewModel.retry()
    advanceUntilIdle()

    assertFalse(viewModel.uiState.value.error)
    assertEquals("r1", viewModel.uiState.value.detail?.id)
    verify(reportRepository, org.mockito.kotlin.times(2)).fetchDetail("r1")
  }
}
