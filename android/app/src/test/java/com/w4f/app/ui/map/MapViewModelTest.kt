package com.w4f.app.ui.map

import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.SyncState
import com.w4f.app.domain.model.WaterSource
import com.w4f.app.testutil.MainDispatcherRule
import java.time.Instant
import java.time.LocalDate
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class MapViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val douarRepository: DouarRepository = mock()
  private val reportRepository: ReportRepository = mock()

  private fun douar(id: String, lat: Double? = 31.0, lon: Double? = -8.0) =
    Douar(id = id, nameAr = "دوار $id", nameFr = "Douar $id", communeId = "c1", lat = lat, lon = lon)

  private fun report(douarId: String, collectedAt: Instant, serverStatus: String?, serverScore: Int? = null) =
    Report(
      id = "$douarId-${collectedAt.toEpochMilli()}",
      douarId = douarId,
      waterSource = WaterSource.WELL,
      problemType = ProblemType.NO_WATER,
      problemStartedOn = LocalDate.of(2026, 1, 1),
      durationDays = 5,
      interruptionFrequency = InterruptionFrequency.DAILY,
      hasAlternativeSource = false,
      alternativeDistanceKm = null,
      severityReported = SeverityLevel.HIGH,
      waterQualityRisk = false,
      affectedFamilies = 3,
      affectedPeople = 10,
      observations = null,
      lat = null,
      lon = null,
      locationAccuracyM = null,
      collectedAt = collectedAt,
      syncState = if (serverStatus == null) SyncState.PENDING else SyncState.SYNCED,
      syncError = null,
      serverStatus = serverStatus,
      serverScore = serverScore,
    )

  private fun viewModel() = MapViewModel(douarRepository, reportRepository)

  @Test
  fun `a douar with no local lat lon is dropped from the markers`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1", lat = null), douar("d2"))))
    whenever(reportRepository.observeReports()).thenReturn(flowOf(emptyList()))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(listOf("d2"), viewModel.uiState.value.markers.map { it.douar.id })
  }

  @Test
  fun `a douar with no reports is NO_REPORTS`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"))))
    whenever(reportRepository.observeReports()).thenReturn(flowOf(emptyList()))

    val viewModel = viewModel()
    advanceUntilIdle()

    val marker = viewModel.uiState.value.markers.single()
    assertEquals(DouarMapStatus.NO_REPORTS, marker.status)
    assertNull(marker.score)
  }

  @Test
  fun `a report not yet synced is PENDING_SYNC`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"))))
    whenever(reportRepository.observeReports())
      .thenReturn(flowOf(listOf(report("d1", Instant.now(), serverStatus = null))))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(DouarMapStatus.PENDING_SYNC, viewModel.uiState.value.markers.single().status)
  }

  @Test
  fun `submitted under_review and recheck_requested all read as AWAITING_REVIEW`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"), douar("d2"), douar("d3"))))
    whenever(reportRepository.observeReports())
      .thenReturn(
        flowOf(
          listOf(
            report("d1", Instant.now(), serverStatus = "submitted"),
            report("d2", Instant.now(), serverStatus = "under_review"),
            report("d3", Instant.now(), serverStatus = "recheck_requested"),
          )
        )
      )

    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.uiState.value.markers.forEach { assertEquals(DouarMapStatus.AWAITING_REVIEW, it.status) }
  }

  @Test
  fun `validated with a score at or above 70 is HIGH_PRIORITY`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"))))
    whenever(reportRepository.observeReports())
      .thenReturn(flowOf(listOf(report("d1", Instant.now(), serverStatus = "validated", serverScore = 70))))

    val viewModel = viewModel()
    advanceUntilIdle()

    val marker = viewModel.uiState.value.markers.single()
    assertEquals(DouarMapStatus.HIGH_PRIORITY, marker.status)
    assertEquals(70, marker.score)
  }

  @Test
  fun `validated below the threshold is VALIDATED, not HIGH_PRIORITY`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"))))
    whenever(reportRepository.observeReports())
      .thenReturn(flowOf(listOf(report("d1", Instant.now(), serverStatus = "validated", serverScore = 69))))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(DouarMapStatus.VALIDATED, viewModel.uiState.value.markers.single().status)
  }

  @Test
  fun `rejected and converted_to_project map to their own statuses`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"), douar("d2"))))
    whenever(reportRepository.observeReports())
      .thenReturn(
        flowOf(
          listOf(
            report("d1", Instant.now(), serverStatus = "rejected"),
            report("d2", Instant.now(), serverStatus = "converted_to_project"),
          )
        )
      )

    val viewModel = viewModel()
    advanceUntilIdle()

    val byDouar = viewModel.uiState.value.markers.associate { it.douar.id to it.status }
    assertEquals(DouarMapStatus.REJECTED, byDouar["d1"])
    assertEquals(DouarMapStatus.PROJECT_UNDERWAY, byDouar["d2"])
  }

  @Test
  fun `a douar's color reflects only its most recently collected report`() = runTest {
    whenever(douarRepository.observeAll()).thenReturn(flowOf(listOf(douar("d1"))))
    whenever(reportRepository.observeReports())
      .thenReturn(
        flowOf(
          listOf(
            report("d1", Instant.ofEpochMilli(1_000), serverStatus = "validated", serverScore = 90),
            report("d1", Instant.ofEpochMilli(2_000), serverStatus = "submitted"),
          )
        )
      )

    val viewModel = viewModel()
    advanceUntilIdle()

    // The newer (submitted) report wins over the older, higher-scoring one.
    assertEquals(DouarMapStatus.AWAITING_REVIEW, viewModel.uiState.value.markers.single().status)
  }
}
