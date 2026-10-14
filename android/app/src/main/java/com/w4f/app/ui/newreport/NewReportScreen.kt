package com.w4f.app.ui.newreport

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import com.w4f.app.ui.newreport.steps.DouarStep
import com.w4f.app.ui.newreport.steps.EvidenceStep
import com.w4f.app.ui.newreport.steps.NumbersStep
import com.w4f.app.ui.newreport.steps.ProblemStep
import com.w4f.app.ui.newreport.steps.SummaryStep

/** Section 8's "تبليغ جديد" stepper: الدوار → المشكل → الأرقام → الإثباتات →
 * ملخص. Each step is its own composable; this host owns the progress bar
 * and back/next/save chrome common to all five. */
@Composable
fun NewReportScreen(
  onDone: () -> Unit,
  onCancel: () -> Unit,
  modifier: Modifier = Modifier,
  viewModel: NewReportViewModel = hiltViewModel(),
) {
  val uiState by viewModel.uiState.collectAsState()

  LaunchedEffect(uiState.savedReportId) {
    if (uiState.savedReportId != null) onDone()
  }

  Column(modifier = modifier.fillMaxSize()) {
    Text(text = stringResource(R.string.new_report_title), style = MaterialTheme.typography.titleLarge)
    Text(
      text =
        stringResource(
          R.string.new_report_step_indicator,
          uiState.step,
          NEW_REPORT_LAST_STEP,
        ),
      style = MaterialTheme.typography.bodySmall,
      modifier = Modifier.padding(top = 4.dp),
    )
    LinearProgressIndicator(
      progress = { uiState.step.toFloat() / NEW_REPORT_LAST_STEP },
      modifier = Modifier.fillMaxWidth().padding(top = 8.dp, bottom = 16.dp),
    )

    Column(modifier = Modifier.weight(1f)) {
      when (uiState.step) {
        1 ->
          DouarStep(
            query = uiState.douarQuery,
            results = uiState.douarResults,
            selected = uiState.selectedDouar,
            onQueryChange = viewModel::onDouarQueryChange,
            onSelect = viewModel::onDouarSelected,
          )
        2 ->
          ProblemStep(
            waterSource = uiState.waterSource,
            problemType = uiState.problemType,
            interruptionFrequency = uiState.interruptionFrequency,
            severityReported = uiState.severityReported,
            waterQualityRisk = uiState.waterQualityRisk,
            onWaterSourceSelected = viewModel::onWaterSourceSelected,
            onProblemTypeSelected = viewModel::onProblemTypeSelected,
            onFrequencySelected = viewModel::onInterruptionFrequencySelected,
            onSeveritySelected = viewModel::onSeveritySelected,
            onWaterQualityRiskToggle = viewModel::onWaterQualityRiskToggle,
          )
        3 ->
          NumbersStep(
            affectedFamilies = uiState.affectedFamilies,
            affectedPeople = uiState.affectedPeople,
            durationDays = uiState.durationDays,
            hasAlternativeSource = uiState.hasAlternativeSource,
            alternativeDistanceKm = uiState.alternativeDistanceKm,
            onAffectedFamiliesChange = viewModel::onAffectedFamiliesChange,
            onAffectedPeopleChange = viewModel::onAffectedPeopleChange,
            onDurationDaysChange = viewModel::onDurationDaysChange,
            onHasAlternativeSourceToggle = viewModel::onHasAlternativeSourceToggle,
            onAlternativeDistanceChange = viewModel::onAlternativeDistanceChange,
          )
        4 ->
          EvidenceStep(
            media = uiState.media,
            location = uiState.location,
            isCapturingLocation = uiState.isCapturingLocation,
            newRawPhotoCaptureFile = viewModel::newRawPhotoCaptureFile,
            newVideoFile = viewModel::newVideoFile,
            onPhotoCaptured = viewModel::onPhotoCaptured,
            onVideoCaptured = viewModel::onVideoCaptured,
            onRemoveMedia = viewModel::onRemoveMedia,
            onCaptureLocation = viewModel::captureLocation,
          )
        else ->
          SummaryStep(
            state = uiState,
            onConfirmSave = viewModel::onConfirmSave,
          )
      }
    }

    Row(modifier = Modifier.fillMaxWidth().padding(top = 16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
      OutlinedButton(onClick = { if (uiState.step == NEW_REPORT_FIRST_STEP) onCancel() else viewModel.onPreviousStep() }) {
        Text(
          stringResource(
            if (uiState.step == NEW_REPORT_FIRST_STEP) R.string.action_cancel else R.string.action_back
          )
        )
      }
      if (uiState.step < NEW_REPORT_LAST_STEP) {
        Button(onClick = viewModel::onNextStep, enabled = uiState.canGoNext) {
          Text(stringResource(R.string.action_next))
        }
      }
    }
  }
}
