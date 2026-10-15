package com.w4f.app.ui.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.repository.NotificationRepository
import com.w4f.app.domain.model.AppNotification
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class NotificationsUiState(val notifications: List<AppNotification> = emptyList())

/** Section 8, screen 5 — "الإشعارات". Room-backed (unlike the dossier
 * detail screen): a notification center is a list the moqaddem should be
 * able to open offline and see what was last synced. */
@HiltViewModel
class NotificationsViewModel @Inject constructor(private val repository: NotificationRepository) :
  ViewModel() {

  private val _uiState = MutableStateFlow(NotificationsUiState())
  val uiState: StateFlow<NotificationsUiState> = _uiState.asStateFlow()

  init {
    viewModelScope.launch {
      repository.observeAll().collect { notifications ->
        _uiState.update { it.copy(notifications = notifications) }
      }
    }
  }

  fun onNotificationClick(notification: AppNotification) {
    if (notification.isRead) return
    viewModelScope.launch { repository.markRead(notification.id) }
  }
}
