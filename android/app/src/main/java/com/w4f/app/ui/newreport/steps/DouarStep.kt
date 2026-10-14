package com.w4f.app.ui.newreport.steps

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.w4f.app.R
import com.w4f.app.domain.model.Douar

/** Section 8, step 1 — "الدوار": searchable, pre-filtered to the
 * moqaddem's own territory (the search itself is scoped in
 * `NewReportViewModel`, against the local Room cache). */
@Composable
fun DouarStep(
  query: String,
  results: List<Douar>,
  selected: Douar?,
  onQueryChange: (String) -> Unit,
  onSelect: (Douar) -> Unit,
) {
  Column(modifier = Modifier.fillMaxWidth()) {
    Text(text = stringResource(R.string.new_report_step1_title), style = MaterialTheme.typography.titleMedium)

    OutlinedTextField(
      value = query,
      onValueChange = onQueryChange,
      label = { Text(stringResource(R.string.new_report_douar_search_label)) },
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
    )

    if (results.isEmpty()) {
      Text(
        text = stringResource(R.string.new_report_douar_empty),
        modifier = Modifier.padding(top = 24.dp),
      )
    } else {
      LazyColumn(modifier = Modifier.padding(top = 8.dp)) {
        items(results, key = { it.id }) { douar ->
          val isSelected = douar.id == selected?.id
          Card(
            onClick = { onSelect(douar) },
            colors =
              if (isSelected) {
                CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
              } else {
                CardDefaults.cardColors()
              },
            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
          ) {
            Column(modifier = Modifier.padding(12.dp)) {
              Text(text = douar.nameAr, style = MaterialTheme.typography.bodyLarge)
              Text(text = douar.nameFr, style = MaterialTheme.typography.bodySmall)
            }
          }
        }
      }
    }
  }
}
