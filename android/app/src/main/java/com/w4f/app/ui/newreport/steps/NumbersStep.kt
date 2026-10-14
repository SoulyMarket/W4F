package com.w4f.app.ui.newreport.steps

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.w4f.app.R

/** Section 8, step 3 — "الأرقام": families, people, duration, alternative
 * source yes/no + distance, all numeric-keypad fields (never free text). */
@Composable
fun NumbersStep(
  affectedFamilies: String,
  affectedPeople: String,
  durationDays: String,
  hasAlternativeSource: Boolean,
  alternativeDistanceKm: String,
  onAffectedFamiliesChange: (String) -> Unit,
  onAffectedPeopleChange: (String) -> Unit,
  onDurationDaysChange: (String) -> Unit,
  onHasAlternativeSourceToggle: (Boolean) -> Unit,
  onAlternativeDistanceChange: (String) -> Unit,
) {
  val numberKeyboard = KeyboardOptions(keyboardType = KeyboardType.Number)

  Column(modifier = Modifier.fillMaxWidth()) {
    Text(text = stringResource(R.string.new_report_step3_title), style = MaterialTheme.typography.titleMedium)

    OutlinedTextField(
      value = affectedFamilies,
      onValueChange = onAffectedFamiliesChange,
      label = { Text(stringResource(R.string.new_report_affected_families_label)) },
      keyboardOptions = numberKeyboard,
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
    )

    OutlinedTextField(
      value = affectedPeople,
      onValueChange = onAffectedPeopleChange,
      label = { Text(stringResource(R.string.new_report_affected_people_label)) },
      keyboardOptions = numberKeyboard,
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    )

    OutlinedTextField(
      value = durationDays,
      onValueChange = onDurationDaysChange,
      label = { Text(stringResource(R.string.new_report_duration_days_label)) },
      keyboardOptions = numberKeyboard,
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    )

    Row(
      verticalAlignment = Alignment.CenterVertically,
      modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
    ) {
      Text(
        text = stringResource(R.string.new_report_has_alternative_source_label),
        modifier = Modifier.weight(1f),
      )
      Switch(checked = hasAlternativeSource, onCheckedChange = onHasAlternativeSourceToggle)
    }

    if (hasAlternativeSource) {
      OutlinedTextField(
        value = alternativeDistanceKm,
        onValueChange = onAlternativeDistanceChange,
        label = { Text(stringResource(R.string.new_report_alternative_distance_label)) },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        singleLine = true,
        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
      )
    }
  }
}
