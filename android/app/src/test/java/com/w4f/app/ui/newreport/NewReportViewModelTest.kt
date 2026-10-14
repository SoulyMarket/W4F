package com.w4f.app.ui.newreport

import com.w4f.app.data.location.CapturedLocation
import com.w4f.app.data.location.LocationClient
import com.w4f.app.data.media.MediaFileStore
import com.w4f.app.data.repository.AuthRepository
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.AppLanguage
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.MediaKind
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportMedia
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.Territory
import com.w4f.app.domain.model.User
import com.w4f.app.domain.model.UserRole
import com.w4f.app.domain.model.WaterSource
import com.w4f.app.sync.SyncScheduler
import com.w4f.app.testutil.MainDispatcherRule
import java.io.File
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.doReturn
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class NewReportViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val douar = Douar(id = "d1", nameAr = "دوار", nameFr = "Douar", communeId = "c1", lat = 31.0, lon = -7.0)
  private val user =
    User(
      id = "u1",
      fullName = "Moqaddem",
      email = "moqaddem@w4f.ma",
      role = UserRole.MOQADDEM,
      preferredLanguage = AppLanguage.AR,
      territories = listOf(Territory(id = "c1", nameAr = "ج", nameFr = "C", level = "commune")),
    )

  private val authRepository: AuthRepository = mock { on { hasSession } doReturn MutableStateFlow(true) }
  private val douarRepository: DouarRepository = mock()
  private val reportRepository: ReportRepository = mock()
  private val locationClient: LocationClient = mock()
  private val mediaFileStore: MediaFileStore = mock()
  private val syncScheduler: SyncScheduler = mock()

  @Before
  fun setUp() {
    runBlocking { whenever(authRepository.currentUser()).thenReturn(Result.success(user)) }
    whenever(douarRepository.search(any(), any())).thenReturn(flowOf(listOf(douar)))
  }

  private fun viewModel() =
    NewReportViewModel(
      authRepository,
      douarRepository,
      reportRepository,
      locationClient,
      mediaFileStore,
      syncScheduler,
    )

  @Test
  fun `initial load resolves the moqaddem's own commune ids and pre-populates douars`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(listOf(douar), viewModel.uiState.value.douarResults)
    verify(douarRepository).search(listOf("c1"), "")
  }

  @Test
  fun `typing a query re-runs the search scoped to the same commune ids`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.onDouarQueryChange("دوار")
    advanceUntilIdle()

    verify(douarRepository).search(eq(listOf("c1")), eq("دوار"))
  }

  @Test
  fun `cannot advance past step 1 without a selected douar`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    assertFalse(viewModel.uiState.value.canGoNext)
    viewModel.onNextStep()
    assertEquals(1, viewModel.uiState.value.step)
  }

  @Test
  fun `selecting a douar allows advancing to the problem step`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.onDouarSelected(douar)
    assertTrue(viewModel.uiState.value.canGoNext)
    viewModel.onNextStep()

    assertEquals(2, viewModel.uiState.value.step)
  }

  @Test
  fun `going back from the first step does not go below it`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.onPreviousStep()

    assertEquals(NEW_REPORT_FIRST_STEP, viewModel.uiState.value.step)
  }

  @Test
  fun `the problem step requires all four selections`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()
    viewModel.onDouarSelected(douar)
    viewModel.onNextStep()

    viewModel.onWaterSourceSelected(WaterSource.WELL)
    viewModel.onProblemTypeSelected(ProblemType.NO_WATER)
    assertFalse(viewModel.uiState.value.canGoNext)

    viewModel.onInterruptionFrequencySelected(InterruptionFrequency.DAILY)
    viewModel.onSeveritySelected(SeverityLevel.HIGH)
    assertTrue(viewModel.uiState.value.canGoNext)
  }

  @Test
  fun `numbers step requires an alternative distance only when a source is marked available`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()
    viewModel.onDouarSelected(douar)
    viewModel.onNextStep()
    viewModel.onWaterSourceSelected(WaterSource.WELL)
    viewModel.onProblemTypeSelected(ProblemType.NO_WATER)
    viewModel.onInterruptionFrequencySelected(InterruptionFrequency.DAILY)
    viewModel.onSeveritySelected(SeverityLevel.HIGH)
    viewModel.onNextStep()

    viewModel.onAffectedFamiliesChange("4")
    viewModel.onAffectedPeopleChange("20")
    viewModel.onDurationDaysChange("10")
    assertTrue(viewModel.uiState.value.canGoNext)

    viewModel.onHasAlternativeSourceToggle(true)
    assertFalse(viewModel.uiState.value.canGoNext)

    viewModel.onAlternativeDistanceChange("3.5")
    assertTrue(viewModel.uiState.value.canGoNext)
  }

  @Test
  fun `non-numeric input is rejected for numeric fields`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.onAffectedFamiliesChange("abc")

    assertEquals("", viewModel.uiState.value.affectedFamilies)
  }

  @Test
  fun `captureLocation toggles the loading flag and stores the result`() = runTest {
    val location = CapturedLocation(lat = 31.3, lon = -7.6, accuracyM = 8f)
    whenever(locationClient.getCurrentLocation()).thenReturn(location)
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.captureLocation()
    advanceUntilIdle()

    assertEquals(location, viewModel.uiState.value.location)
    assertFalse(viewModel.uiState.value.isCapturingLocation)
  }

  @Test
  fun `a missing GPS fix never blocks the evidence step`() = runTest {
    whenever(locationClient.getCurrentLocation()).thenReturn(null)
    val viewModel = viewModel()
    advanceUntilIdle()
    viewModel.onDouarSelected(douar)
    viewModel.onNextStep()
    viewModel.onWaterSourceSelected(WaterSource.WELL)
    viewModel.onProblemTypeSelected(ProblemType.NO_WATER)
    viewModel.onInterruptionFrequencySelected(InterruptionFrequency.DAILY)
    viewModel.onSeveritySelected(SeverityLevel.HIGH)
    viewModel.onNextStep()
    viewModel.onAffectedFamiliesChange("4")
    viewModel.onAffectedPeopleChange("20")
    viewModel.onDurationDaysChange("10")
    viewModel.onNextStep()

    viewModel.captureLocation()
    advanceUntilIdle()

    assertEquals(4, viewModel.uiState.value.step)
    assertNull(viewModel.uiState.value.location)
    assertTrue(viewModel.uiState.value.canGoNext)
  }

  @Test
  fun `onVideoCaptured appends a pending media draft`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()
    val file = File("/tmp/video.mp4")

    viewModel.onVideoCaptured(file)

    val media = viewModel.uiState.value.media
    assertEquals(1, media.size)
    assertEquals(MediaKind.VIDEO, media[0].kind)
    assertEquals(file.absolutePath, media[0].localUri)
  }

  @Test
  fun `removing media drops only the matching entry`() = runTest {
    val fileB = File("/tmp/b.mp4")
    val viewModel = viewModel()
    advanceUntilIdle()
    viewModel.onVideoCaptured(File("/tmp/a.mp4"))
    viewModel.onVideoCaptured(fileB)
    val idToRemove = viewModel.uiState.value.media[0].id

    viewModel.onRemoveMedia(idToRemove)

    val remaining = viewModel.uiState.value.media
    assertEquals(1, remaining.size)
    assertEquals(fileB.absolutePath, remaining[0].localUri)
  }

  @Test
  fun `confirming save with an incomplete draft does nothing`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()

    viewModel.onConfirmSave()
    advanceUntilIdle()

    assertNull(viewModel.uiState.value.savedReportId)
    verify(reportRepository, org.mockito.kotlin.never()).saveNewReport(any(), any())
  }

  @Test
  fun `confirming save with a complete draft persists the report and media as pending`() = runTest {
    val viewModel = viewModel()
    advanceUntilIdle()
    viewModel.onDouarSelected(douar)
    viewModel.onNextStep()
    viewModel.onWaterSourceSelected(WaterSource.WELL)
    viewModel.onProblemTypeSelected(ProblemType.NO_WATER)
    viewModel.onInterruptionFrequencySelected(InterruptionFrequency.DAILY)
    viewModel.onSeveritySelected(SeverityLevel.HIGH)
    viewModel.onNextStep()
    viewModel.onAffectedFamiliesChange("4")
    viewModel.onAffectedPeopleChange("20")
    viewModel.onDurationDaysChange("10")
    viewModel.onNextStep()
    viewModel.onVideoCaptured(File("/tmp/evidence.mp4"))
    viewModel.onNextStep()

    viewModel.onConfirmSave()
    advanceUntilIdle()

    val reportCaptor = org.mockito.kotlin.argumentCaptor<Report>()
    val mediaCaptor = org.mockito.kotlin.argumentCaptor<List<ReportMedia>>()
    verify(reportRepository).saveNewReport(reportCaptor.capture(), mediaCaptor.capture())

    val savedReport = reportCaptor.firstValue
    assertEquals(douar.id, savedReport.douarId)
    assertEquals(WaterSource.WELL, savedReport.waterSource)
    assertEquals(10, savedReport.durationDays)
    assertEquals(com.w4f.app.domain.model.SyncState.PENDING, savedReport.syncState)
    assertEquals(savedReport.id, viewModel.uiState.value.savedReportId)

    val savedMedia = mediaCaptor.firstValue
    assertEquals(1, savedMedia.size)
    assertEquals(savedReport.id, savedMedia[0].reportId)
    assertEquals(com.w4f.app.domain.model.SyncState.PENDING, savedMedia[0].syncState)
  }
}
