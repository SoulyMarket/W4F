package com.w4f.app.ui.home

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
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

// Full dossier list + sync status bar land in step 2.4; this is the
// post-login landing stub step 2.2 needs to prove the auth/nav flow works,
// now with the "تبليغ جديد" entry point step 2.3 adds.
@Composable
fun HomeScreen(
  onLoggedOut: () -> Unit,
  onNewReportClick: () -> Unit,
  modifier: Modifier = Modifier,
  viewModel: HomeViewModel = hiltViewModel(),
) {
  val uiState by viewModel.uiState.collectAsState()

  LaunchedEffect(uiState.loggedOut) {
    if (uiState.loggedOut) onLoggedOut()
  }

  Column(modifier = modifier.fillMaxSize().padding(24.dp)) {
    Text(text = stringResource(R.string.home_title), style = MaterialTheme.typography.titleLarge)
    uiState.fullName?.let { name -> Text(text = name, modifier = Modifier.padding(top = 8.dp)) }
    Button(
      onClick = onNewReportClick,
      modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
    ) {
      Text(stringResource(R.string.home_new_report))
    }
    Button(onClick = viewModel::onLogoutClick, modifier = Modifier.padding(top = 12.dp)) {
      Text(stringResource(R.string.settings_logout))
    }
  }
}
