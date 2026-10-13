package com.w4f.app.ui.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.w4f.app.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(onLoginSuccess: () -> Unit, modifier: Modifier = Modifier, viewModel: LoginViewModel = hiltViewModel()) {
  val uiState by viewModel.uiState.collectAsState()

  LaunchedEffect(uiState.loginSucceeded) {
    if (uiState.loginSucceeded) onLoginSuccess()
  }

  Column(
    modifier = modifier.fillMaxSize().padding(24.dp),
    verticalArrangement = Arrangement.Center,
  ) {
    Text(text = stringResource(R.string.login_title), style = MaterialTheme.typography.titleLarge)

    OutlinedTextField(
      value = uiState.email,
      onValueChange = viewModel::onEmailChange,
      label = { Text(stringResource(R.string.login_email_label)) },
      keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
    )

    OutlinedTextField(
      value = uiState.password,
      onValueChange = viewModel::onPasswordChange,
      label = { Text(stringResource(R.string.login_password_label)) },
      visualTransformation = PasswordVisualTransformation(),
      keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
      singleLine = true,
      modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
    )

    uiState.error?.let { error ->
      Text(
        text = stringResource(error.toStringRes()),
        color = MaterialTheme.colorScheme.error,
        modifier = Modifier.padding(top = 8.dp),
      )
    }

    Button(
      onClick = viewModel::onLoginClick,
      enabled = !uiState.isLoading && uiState.email.isNotBlank() && uiState.password.isNotBlank(),
      modifier = Modifier.fillMaxWidth().padding(top = 24.dp),
    ) {
      if (uiState.isLoading) {
        CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
      }
      Text(stringResource(R.string.login_submit))
    }
  }
}

private fun LoginErrorType.toStringRes(): Int =
  when (this) {
    LoginErrorType.INVALID_CREDENTIALS -> R.string.login_error_invalid_credentials
    LoginErrorType.ACCOUNT_LOCKED -> R.string.login_error_account_locked
    LoginErrorType.ACCOUNT_INACTIVE -> R.string.login_error_account_inactive
    LoginErrorType.NETWORK -> R.string.login_error_network
    LoginErrorType.GENERIC -> R.string.login_error_generic
  }
