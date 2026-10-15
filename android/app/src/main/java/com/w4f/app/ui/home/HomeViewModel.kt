package com.w4f.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.local.NetworkMonitor
import com.w4f.app.data.repository.AuthRepository
import com.w4f.app.data.repository.NotificationRepository
import com.w4f.app.data.repository.ReportRepository
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.SyncState
import com.w4f.app.sync.SyncScheduler
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Section 8, screen 2's three-state sync bar: «كل شيء متزامن» / «N في
 * الانتظار» / «بدون اتصال». Deliberately coarse — "syncing right now" and
 * "queued, about to sync" both read as [PENDING]; the spec's own bar only
 * has these three states, nothing in between. */
enum class SyncStatus {
  ALL_SYNCED,
  PENDING,
  OFFLINE,
}

data class HomeUiState(
  val fullName: String? = null,
  val loggedOut: Boolean = false,
  val reports: List<Report> = emptyList(),
  val syncStatus: SyncStatus = SyncStatus.ALL_SYNCED,
  val pendingCount: Int = 0,
  val unreadNotificationCount: Int = 0,
)

@HiltViewModel
class HomeViewModel
@Inject
constructor(
  private val authRepository: AuthRepository,
  private val reportRepository: ReportRepository,
  private val notificationRepository: NotificationRepository,
  private val networkMonitor: NetworkMonitor,
  private val syncScheduler: SyncScheduler,
) : ViewModel() {

  private val _uiState = MutableStateFlow(HomeUiState())
  val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

  init {
    viewModelScope.launch {
      authRepository.currentUser().onSuccess { user ->
        _uiState.update { it.copy(fullName = user.fullName) }
      }
    }
    // Section 8 lists "on save / periodically / on sync now" as the sync
    // triggers, but a fresh login has nothing pending to save yet — without
    // this, reference data (douars) only ever arrives after the first
    // periodic tick, up to 15 minutes later. Kicking a sync on every Home
    // entry (not just first login) is cheap and idempotent (syncNow()
    // replaces any in-flight request rather than stacking).
    syncScheduler.syncNow()
    viewModelScope.launch {
      combine(reportRepository.observeReports(), networkMonitor.isConnected) { reports, connected ->
          val pendingCount =
            reports.count { it.syncState == SyncState.PENDING || it.syncState == SyncState.FAILED }
          val status =
            when {
              pendingCount == 0 -> SyncStatus.ALL_SYNCED
              connected -> SyncStatus.PENDING
              else -> SyncStatus.OFFLINE
            }
          Triple(reports, status, pendingCount)
        }
        .collect { (reports, status, pendingCount) ->
          _uiState.update { it.copy(reports = reports, syncStatus = status, pendingCount = pendingCount) }
        }
    }
    viewModelScope.launch {
      notificationRepository.observeUnreadCount().collect { count ->
        _uiState.update { it.copy(unreadNotificationCount = count) }
      }
    }
  }

  fun onLogoutClick() {
    viewModelScope.launch {
      authRepository.logout()
      _uiState.update { it.copy(loggedOut = true) }
    }
  }

  fun onSyncNowClick() {
    syncScheduler.syncNow()
  }
}
