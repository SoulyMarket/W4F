package com.w4f.app.ui.dossierdetail

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.w4f.app.R
import com.w4f.app.domain.model.ReportDetail
import com.w4f.app.domain.model.ValidationRecord
import com.w4f.app.ui.common.labelRes
import com.w4f.app.ui.common.projectStatusLabelRes
import com.w4f.app.ui.common.reportStatusLabelRes
import com.w4f.app.ui.common.validationDecisionLabelRes

@Composable
fun DossierDetailScreen(reportId: String, modifier: Modifier = Modifier, viewModel: DossierDetailViewModel = hiltViewModel()) {
  val uiState by viewModel.uiState.collectAsState()

  LaunchedEffect(reportId) { viewModel.load(reportId) }

  Column(modifier = modifier.fillMaxSize()) {
    Text(text = stringResource(R.string.dossier_detail_title), style = MaterialTheme.typography.titleLarge)

    when {
      uiState.isLoading ->
        CircularProgressIndicator(modifier = Modifier.padding(top = 32.dp))
      uiState.error ->
        Column(modifier = Modifier.padding(top = 16.dp)) {
          Text(stringResource(R.string.dossier_detail_loading_error))
          Button(onClick = viewModel::retry, modifier = Modifier.padding(top = 8.dp)) {
            Text(stringResource(R.string.action_retry))
          }
        }
      uiState.detail != null ->
        DossierDetailContent(detail = uiState.detail!!, douarName = uiState.douarName)
    }
  }
}

@Composable
private fun DossierDetailContent(detail: ReportDetail, douarName: String?) {
  LazyColumn(modifier = Modifier.fillMaxSize().padding(top = 16.dp)) {
    item { SectionTitle(R.string.dossier_detail_data_section) }
    item {
      Column {
        douarName?.let { Text(it, style = MaterialTheme.typography.bodyLarge) }
        Text(stringResource(detail.problemType.labelRes()))
        Text(stringResource(detail.waterSource.labelRes()))
        Text(stringResource(detail.interruptionFrequency.labelRes()))
        Text(stringResource(detail.severityReported.labelRes()))
        detail.observations?.let { Text(it, modifier = Modifier.padding(top = 8.dp)) }
        val statusLabelRes = reportStatusLabelRes(detail.status)
        Text(
          text = statusLabelRes?.let { stringResource(it) } ?: detail.status,
          style = MaterialTheme.typography.labelLarge,
          modifier = Modifier.padding(top = 8.dp),
        )
      }
    }

    item { SectionDivider() }
    item { SectionTitle(R.string.dossier_detail_media_section) }
    if (detail.media.isEmpty()) {
      item { Text(stringResource(R.string.dossier_detail_no_media)) }
    } else {
      items(detail.media, key = { it.id }) { media ->
        Text("${media.kind} — ${media.uploadStatus}", modifier = Modifier.padding(vertical = 2.dp))
      }
    }

    item { SectionDivider() }
    item { SectionTitle(R.string.dossier_detail_priority_section) }
    item {
      val priority = detail.priority
      if (priority == null) {
        Text(stringResource(R.string.dossier_detail_no_priority))
      } else {
        Column {
          Text("${priority.score}", style = MaterialTheme.typography.headlineMedium)
          Text(
            stringResource(R.string.dossier_detail_why_priority),
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(top = 8.dp),
          )
          priority.breakdown.forEach { entry ->
            Row(modifier = Modifier.fillMaxWidth().padding(top = 4.dp)) {
              Text(entry.reason, modifier = Modifier.weight(1f))
              Text("+${entry.points.toInt()}")
            }
          }
        }
      }
    }

    item { SectionDivider() }
    item { SectionTitle(R.string.dossier_detail_validations_section) }
    if (detail.validations.isEmpty()) {
      item { Text(stringResource(R.string.dossier_detail_no_validations)) }
    } else {
      items(detail.validations, key = { it.id }) { validation -> ValidationRow(validation) }
    }

    if (detail.project != null) {
      item { SectionDivider() }
      item { SectionTitle(R.string.dossier_detail_project_section) }
      item {
        val project = detail.project
        Column {
          Text(project.title, style = MaterialTheme.typography.bodyLarge)
          val statusLabelRes = projectStatusLabelRes(project.status)
          Text(statusLabelRes?.let { stringResource(it) } ?: project.status)
          Text(stringResource(R.string.dossier_detail_project_progress, project.progressPercent))
        }
      }
    }
  }
}

@Composable
private fun ValidationRow(validation: ValidationRecord) {
  Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
    Column(modifier = Modifier.padding(12.dp)) {
      val decisionLabelRes = validationDecisionLabelRes(validation.decision)
      val isRecheck = validation.decision == "recheck_requested"
      Text(
        text = decisionLabelRes?.let { stringResource(it) } ?: validation.decision,
        style = MaterialTheme.typography.labelLarge,
        color = if (isRecheck) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface,
      )
      if (isRecheck) {
        Text(
          stringResource(R.string.dossier_detail_recheck_highlight),
          color = MaterialTheme.colorScheme.error,
          style = MaterialTheme.typography.bodySmall,
        )
      }
      validation.comment?.let { Text(it, modifier = Modifier.padding(top = 4.dp)) }
      validation.proposedSolution?.let { Text(it, modifier = Modifier.padding(top = 4.dp)) }
    }
  }
}

@Composable
private fun SectionTitle(textRes: Int) {
  Text(
    text = stringResource(textRes),
    style = MaterialTheme.typography.titleMedium,
    modifier = Modifier.padding(bottom = 8.dp),
  )
}

@Composable
private fun SectionDivider() {
  HorizontalDivider(modifier = Modifier.padding(vertical = 16.dp))
}
