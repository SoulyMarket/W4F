package com.w4f.app.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.w4f.app.R
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.SyncState
import com.w4f.app.ui.common.labelRes

// Section 8, screen 2 (الرئيسية): big "تبليغ جديد" button, dossier list
// with status chips, sync status bar. Dossier *detail* (tapping an item)
// is step 2.5's job — this is the list view only.
@Composable
fun HomeScreen(
  onLoggedOut: () -> Unit,
  onNewReportClick: () -> Unit,
  onReportClick: (String) -> Unit,
  onNotificationsClick: () -> Unit,
  modifier: Modifier = Modifier,
  viewModel: HomeViewModel = hiltViewModel(),
) {
  val uiState by viewModel.uiState.collectAsState()

  LaunchedEffect(uiState.loggedOut) {
    if (uiState.loggedOut) onLoggedOut()
  }

  Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
      Text(
        text = stringResource(R.string.home_title),
        style = MaterialTheme.typography.titleLarge,
        modifier = Modifier.weight(1f),
      )
      TextButton(onClick = onNotificationsClick) {
        Text(stringResource(R.string.home_notifications, uiState.unreadNotificationCount))
      }
    }
    uiState.fullName?.let { name -> Text(text = name, modifier = Modifier.padding(top = 8.dp)) }

    Button(onClick = onNewReportClick, modifier = Modifier.fillMaxWidth().padding(top = 24.dp)) {
      Text(stringResource(R.string.home_new_report))
    }

    SyncStatusBar(
      status = uiState.syncStatus,
      pendingCount = uiState.pendingCount,
      onSyncNowClick = viewModel::onSyncNowClick,
      modifier = Modifier.padding(top = 16.dp),
    )

    if (uiState.reports.isEmpty()) {
      Text(
        text = stringResource(R.string.home_dossiers_empty),
        modifier = Modifier.padding(top = 32.dp),
      )
    } else {
      LazyColumn(modifier = Modifier.weight(1f).padding(top = 16.dp)) {
        items(uiState.reports, key = { it.id }) { report ->
          DossierListItem(report, onClick = { onReportClick(report.id) })
        }
      }
    }

    Button(onClick = viewModel::onLogoutClick, modifier = Modifier.padding(top = 12.dp)) {
      Text(stringResource(R.string.settings_logout))
    }
  }
}

@Composable
private fun SyncStatusBar(
  status: SyncStatus,
  pendingCount: Int,
  onSyncNowClick: () -> Unit,
  modifier: Modifier = Modifier,
) {
  Surface(
    color = MaterialTheme.colorScheme.surfaceVariant,
    modifier = modifier.fillMaxWidth(),
  ) {
    Row(
      verticalAlignment = Alignment.CenterVertically,
      modifier = Modifier.fillMaxWidth().padding(12.dp),
    ) {
      val label =
        when (status) {
          SyncStatus.ALL_SYNCED -> stringResource(R.string.home_sync_all_synced)
          SyncStatus.PENDING -> stringResource(R.string.home_sync_pending, pendingCount)
          SyncStatus.OFFLINE -> stringResource(R.string.home_sync_offline)
        }
      Text(text = label, modifier = Modifier.weight(1f))
      // Always available, not just when something is pending (section 8,
      // screen 7: "sync now" is a standing action) — also the only way to
      // trigger the first-ever pull on a fresh login before anything local
      // is pending.
      TextButton(onClick = onSyncNowClick) { Text(stringResource(R.string.home_sync_now)) }
    }
  }
}

@Composable
private fun DossierListItem(report: Report, onClick: () -> Unit) {
  Card(onClick = onClick, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
    Row(
      verticalAlignment = Alignment.CenterVertically,
      modifier = Modifier.fillMaxWidth().padding(12.dp),
    ) {
      Text(text = stringResource(report.problemType.labelRes()), modifier = Modifier.weight(1f))
      Text(text = stringResource(report.statusChipLabelRes()), style = MaterialTheme.typography.labelMedium)
    }
  }
}

private fun Report.statusChipLabelRes(): Int =
  when (syncState) {
    SyncState.PENDING, SyncState.SYNCING -> R.string.dossier_status_pending
    SyncState.FAILED -> R.string.dossier_status_failed
    SyncState.REJECTED -> R.string.dossier_status_rejected
    // Section 2.5 (dossier detail) is where the full server-status label
    // (submitted/validated/etc.) lands — this list view only needs
    // "it made it to the server" until then.
    SyncState.SYNCED -> R.string.dossier_status_synced
  }
