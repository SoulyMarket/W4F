package com.w4f.app.ui.notifications

import com.w4f.app.data.repository.NotificationRepository
import com.w4f.app.domain.model.AppNotification
import com.w4f.app.testutil.MainDispatcherRule
import java.time.Instant
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class NotificationsViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val repository: NotificationRepository = mock()

  private fun notification(id: String, isRead: Boolean) =
    AppNotification(
      id = id,
      type = "validated",
      entityType = "report",
      entityId = "r1",
      isRead = isRead,
      createdAt = Instant.now(),
      message = "تم التحقق من بلاغكم",
    )

  @Test
  fun `loads notifications from the repository`() = runTest {
    whenever(repository.observeAll()).thenReturn(flowOf(listOf(notification("n1", isRead = false))))
    val viewModel = NotificationsViewModel(repository)

    advanceUntilIdle()

    assertEquals(1, viewModel.uiState.value.notifications.size)
  }

  @Test
  fun `tapping an unread notification marks it read`() = runTest {
    whenever(repository.observeAll()).thenReturn(flowOf(listOf(notification("n1", isRead = false))))
    val viewModel = NotificationsViewModel(repository)
    advanceUntilIdle()

    viewModel.onNotificationClick(notification("n1", isRead = false))
    advanceUntilIdle()

    verify(repository).markRead("n1")
  }

  @Test
  fun `tapping an already-read notification does nothing`() = runTest {
    whenever(repository.observeAll()).thenReturn(flowOf(listOf(notification("n1", isRead = true))))
    val viewModel = NotificationsViewModel(repository)
    advanceUntilIdle()

    viewModel.onNotificationClick(notification("n1", isRead = true))
    advanceUntilIdle()

    verify(repository, never()).markRead(org.mockito.kotlin.any())
  }
}
