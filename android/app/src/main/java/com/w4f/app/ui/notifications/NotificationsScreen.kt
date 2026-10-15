package com.w4f.app.ui.notifications

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.w4f.app.R
import com.w4f.app.domain.model.AppNotification
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Composable
fun NotificationsScreen(modifier: Modifier = Modifier, viewModel: NotificationsViewModel = hiltViewModel()) {
  val uiState by viewModel.uiState.collectAsState()

  Column(modifier = modifier.fillMaxSize()) {
    Text(text = stringResource(R.string.notifications_title), style = MaterialTheme.typography.titleLarge)

    if (uiState.notifications.isEmpty()) {
      Text(
        text = stringResource(R.string.notifications_empty),
        modifier = Modifier.padding(top = 32.dp),
      )
    } else {
      LazyColumn(modifier = Modifier.padding(top = 16.dp)) {
        items(uiState.notifications, key = { it.id }) { notification ->
          NotificationRow(notification, onClick = { viewModel.onNotificationClick(notification) })
        }
      }
    }
  }
}

private val TIMESTAMP_FORMATTER =
  DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm").withZone(ZoneId.systemDefault())

@Composable
private fun NotificationRow(notification: AppNotification, onClick: () -> Unit) {
  Card(
    onClick = onClick,
    colors =
      if (notification.isRead) {
        CardDefaults.cardColors()
      } else {
        CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
      },
    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
  ) {
    Column(modifier = Modifier.padding(12.dp)) {
      Text(text = notification.message, style = MaterialTheme.typography.bodyLarge)
      Text(
        text = TIMESTAMP_FORMATTER.format(notification.createdAt),
        style = MaterialTheme.typography.labelSmall,
        modifier = Modifier.padding(top = 4.dp),
      )
    }
  }
}
