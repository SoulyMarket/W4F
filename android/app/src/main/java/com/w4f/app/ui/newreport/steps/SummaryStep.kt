package com.w4f.app.ui.newreport.steps

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.w4f.app.R
import com.w4f.app.ui.newreport.NewReportUiState

/** Section 8, step 5 — "ملخص": summary + confirmation dialog before saving.
 * The actual local save (and its `sync_state = pending`) happens only after
 * the moqaddem confirms here. */
@Composable
fun SummaryStep(state: NewReportUiState, onConfirmSave: () -> Unit) {
  var showConfirmDialog by remember { mutableStateOf(false) }

  Column(modifier = Modifier.fillMaxWidth()) {
    Text(text = stringResource(R.string.new_report_step5_title), style = MaterialTheme.typography.titleMedium)

    SummaryRow(R.string.new_report_summary_douar, state.selectedDouar?.nameAr ?: "")
    SummaryRow(R.string.new_report_summary_problem, state.problemType?.name ?: "")
    SummaryRow(
      R.string.new_report_summary_people,
      state.affectedPeople.ifBlank { "0" },
    )
    Text(
      text = stringResource(R.string.new_report_summary_media_count, state.media.size),
      modifier = Modifier.padding(top = 12.dp),
    )

    Button(
      onClick = { showConfirmDialog = true },
      enabled = state.isReadyToSave && !state.isSaving,
      modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
    ) {
      if (state.isSaving) {
        CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
      }
      Text(stringResource(R.string.new_report_confirm_save))
    }
  }

  if (showConfirmDialog) {
    AlertDialog(
      onDismissRequest = { showConfirmDialog = false },
      title = { Text(stringResource(R.string.new_report_save_dialog_title)) },
      text = { Text(stringResource(R.string.new_report_save_dialog_message)) },
      confirmButton = {
        TextButton(
          onClick = {
            showConfirmDialog = false
            onConfirmSave()
          }
        ) {
          Text(stringResource(R.string.action_save))
        }
      },
      dismissButton = {
        TextButton(onClick = { showConfirmDialog = false }) { Text(stringResource(R.string.action_cancel)) }
      },
    )
  }
}

@Composable
private fun SummaryRow(labelRes: Int, value: String) {
  Column(modifier = Modifier.padding(top = 12.dp)) {
    Text(text = stringResource(labelRes), style = MaterialTheme.typography.labelLarge)
    Text(text = value, style = MaterialTheme.typography.bodyLarge)
  }
}
