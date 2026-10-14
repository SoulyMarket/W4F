package com.w4f.app.ui.home

import com.w4f.app.data.local.NetworkMonitor
import com.w4f.app.data.repository.AuthRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.AppLanguage
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.SyncState
import com.w4f.app.domain.model.User
import com.w4f.app.domain.model.UserRole
import com.w4f.app.domain.model.WaterSource
import com.w4f.app.sync.SyncScheduler
import com.w4f.app.testutil.MainDispatcherRule
import java.time.Instant
import java.time.LocalDate
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.atLeastOnce
import org.mockito.kotlin.doReturn
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val authRepository: AuthRepository = mock { on { hasSession } doReturn MutableStateFlow(true) }
  private val reportRepository: ReportRepository = mock()
  private val networkMonitor: NetworkMonitor = mock()
  private val syncScheduler: SyncScheduler = mock()

  private val user =
    User(
      id = "u1",
      fullName = "Moqaddem",
      email = "moqaddem@w4f.ma",
      role = UserRole.MOQADDEM,
      preferredLanguage = AppLanguage.AR,
      territories = emptyList(),
    )

  @Before
  fun setUp() {
    runBlocking { whenever(authRepository.currentUser()).thenReturn(Result.success(user)) }
  }

  private fun report(syncState: SyncState) =
    Report(
      id = "r1",
      douarId = "d1",
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
      collectedAt = Instant.now(),
      syncState = syncState,
      syncError = null,
      serverStatus = null,
      serverScore = null,
    )

  private fun viewModel() = HomeViewModel(authRepository, reportRepository, networkMonitor, syncScheduler)

  @Test
  fun `no pending or failed reports means everything is synced`() = runTest {
    whenever(reportRepository.observeReports()).thenReturn(flowOf(listOf(report(SyncState.SYNCED))))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(true))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(SyncStatus.ALL_SYNCED, viewModel.uiState.value.syncStatus)
    assertEquals(0, viewModel.uiState.value.pendingCount)
  }

  @Test
  fun `pending reports while connected shows the pending count`() = runTest {
    whenever(reportRepository.observeReports())
      .thenReturn(flowOf(listOf(report(SyncState.PENDING), report(SyncState.SYNCED))))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(true))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(SyncStatus.PENDING, viewModel.uiState.value.syncStatus)
    assertEquals(1, viewModel.uiState.value.pendingCount)
  }

  @Test
  fun `pending reports while offline shows offline instead of pending`() = runTest {
    whenever(reportRepository.observeReports()).thenReturn(flowOf(listOf(report(SyncState.PENDING))))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(false))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(SyncStatus.OFFLINE, viewModel.uiState.value.syncStatus)
  }

  @Test
  fun `a failed report counts the same as pending`() = runTest {
    whenever(reportRepository.observeReports()).thenReturn(flowOf(listOf(report(SyncState.FAILED))))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(true))

    val viewModel = viewModel()
    advanceUntilIdle()

    assertEquals(SyncStatus.PENDING, viewModel.uiState.value.syncStatus)
    assertEquals(1, viewModel.uiState.value.pendingCount)
  }

  @Test
  fun `entering the home screen kicks an immediate sync`() = runTest {
    whenever(reportRepository.observeReports()).thenReturn(flowOf(emptyList()))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(true))

    viewModel()
    advanceUntilIdle()

    // A fresh login has nothing pending yet (no reports to push), so this
    // is the only thing that would ever pull reference data (douars)
    // without waiting on the 15-minute periodic tick.
    verify(syncScheduler, atLeastOnce()).syncNow()
  }

  @Test
  fun `sync now delegates to the scheduler`() = runTest {
    whenever(reportRepository.observeReports()).thenReturn(flowOf(emptyList()))
    whenever(networkMonitor.isConnected).thenReturn(flowOf(true))
    val viewModel = viewModel()
    advanceUntilIdle()
    org.mockito.kotlin.clearInvocations(syncScheduler)

    viewModel.onSyncNowClick()

    verify(syncScheduler).syncNow()
  }
}
