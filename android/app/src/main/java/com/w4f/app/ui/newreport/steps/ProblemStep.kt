package com.w4f.app.ui.newreport.steps

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.w4f.app.R
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.WaterSource

/** Section 8, step 2 — "المشكل": chips with icons for type, source,
 * frequency, severity (icons land with the final design pass; the chip
 * interaction and i18n coverage are what step 2.3 needs to prove). */
@Composable
fun ProblemStep(
  waterSource: WaterSource?,
  problemType: ProblemType?,
  interruptionFrequency: InterruptionFrequency?,
  severityReported: SeverityLevel?,
  waterQualityRisk: Boolean,
  onWaterSourceSelected: (WaterSource) -> Unit,
  onProblemTypeSelected: (ProblemType) -> Unit,
  onFrequencySelected: (InterruptionFrequency) -> Unit,
  onSeveritySelected: (SeverityLevel) -> Unit,
  onWaterQualityRiskToggle: (Boolean) -> Unit,
) {
  Column(modifier = Modifier.fillMaxWidth()) {
    Text(text = stringResource(R.string.new_report_step2_title), style = MaterialTheme.typography.titleMedium)

    ChipGroupLabel(R.string.new_report_water_source_label)
    FlowRow {
      WaterSource.entries.forEach { value ->
        FilterChip(
          selected = value == waterSource,
          onClick = { onWaterSourceSelected(value) },
          label = { Text(stringResource(value.labelRes())) },
          modifier = Modifier.padding(end = 8.dp, bottom = 8.dp),
        )
      }
    }

    ChipGroupLabel(R.string.new_report_problem_type_label)
    FlowRow {
      ProblemType.entries.forEach { value ->
        FilterChip(
          selected = value == problemType,
          onClick = { onProblemTypeSelected(value) },
          label = { Text(stringResource(value.labelRes())) },
          modifier = Modifier.padding(end = 8.dp, bottom = 8.dp),
        )
      }
    }

    ChipGroupLabel(R.string.new_report_frequency_label)
    FlowRow {
      InterruptionFrequency.entries.forEach { value ->
        FilterChip(
          selected = value == interruptionFrequency,
          onClick = { onFrequencySelected(value) },
          label = { Text(stringResource(value.labelRes())) },
          modifier = Modifier.padding(end = 8.dp, bottom = 8.dp),
        )
      }
    }

    ChipGroupLabel(R.string.new_report_severity_label)
    FlowRow {
      SeverityLevel.entries.forEach { value ->
        FilterChip(
          selected = value == severityReported,
          onClick = { onSeveritySelected(value) },
          label = { Text(stringResource(value.labelRes())) },
          modifier = Modifier.padding(end = 8.dp, bottom = 8.dp),
        )
      }
    }

    Row(
      verticalAlignment = Alignment.CenterVertically,
      modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
    ) {
      Text(
        text = stringResource(R.string.new_report_water_quality_risk_label),
        modifier = Modifier.weight(1f),
      )
      Switch(checked = waterQualityRisk, onCheckedChange = onWaterQualityRiskToggle)
    }
  }
}

@Composable
private fun ChipGroupLabel(labelRes: Int) {
  Text(
    text = stringResource(labelRes),
    style = MaterialTheme.typography.labelLarge,
    modifier = Modifier.padding(top = 16.dp, bottom = 8.dp),
  )
}

private fun WaterSource.labelRes(): Int =
  when (this) {
    WaterSource.NETWORK -> R.string.water_source_network
    WaterSource.WELL -> R.string.water_source_well
    WaterSource.SPRING -> R.string.water_source_spring
    WaterSource.TANK_TRUCK -> R.string.water_source_tank_truck
    WaterSource.RIVER -> R.string.water_source_river
    WaterSource.OTHER -> R.string.water_source_other
  }

private fun ProblemType.labelRes(): Int =
  when (this) {
    ProblemType.NO_WATER -> R.string.problem_type_no_water
    ProblemType.INTERMITTENT -> R.string.problem_type_intermittent
    ProblemType.LOW_PRESSURE -> R.string.problem_type_low_pressure
    ProblemType.CONTAMINATION -> R.string.problem_type_contamination
    ProblemType.BROKEN_PUMP -> R.string.problem_type_broken_pump
    ProblemType.BROKEN_PIPE -> R.string.problem_type_broken_pipe
    ProblemType.DRY_SOURCE -> R.string.problem_type_dry_source
    ProblemType.OTHER -> R.string.problem_type_other
  }

private fun InterruptionFrequency.labelRes(): Int =
  when (this) {
    InterruptionFrequency.PERMANENT -> R.string.frequency_permanent
    InterruptionFrequency.DAILY -> R.string.frequency_daily
    InterruptionFrequency.WEEKLY -> R.string.frequency_weekly
    InterruptionFrequency.MONTHLY -> R.string.frequency_monthly
    InterruptionFrequency.RARE -> R.string.frequency_rare
  }

private fun SeverityLevel.labelRes(): Int =
  when (this) {
    SeverityLevel.LOW -> R.string.severity_low
    SeverityLevel.MEDIUM -> R.string.severity_medium
    SeverityLevel.HIGH -> R.string.severity_high
    SeverityLevel.CRITICAL -> R.string.severity_critical
  }
