package com.w4f.app.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.remote.ApiException
import com.w4f.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.io.IOException
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class LoginErrorType {
  INVALID_CREDENTIALS,
  ACCOUNT_LOCKED,
  ACCOUNT_INACTIVE,
  NETWORK,
  GENERIC,
}

data class LoginUiState(
  val email: String = "",
  val password: String = "",
  val isLoading: Boolean = false,
  val error: LoginErrorType? = null,
  val loginSucceeded: Boolean = false,
)

@HiltViewModel
class LoginViewModel @Inject constructor(private val authRepository: AuthRepository) : ViewModel() {

  private val _uiState = MutableStateFlow(LoginUiState())
  val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

  fun onEmailChange(value: String) {
    _uiState.update { it.copy(email = value, error = null) }
  }

  fun onPasswordChange(value: String) {
    _uiState.update { it.copy(password = value, error = null) }
  }

  fun onLoginClick() {
    val state = _uiState.value
    if (state.email.isBlank() || state.password.isBlank()) return

    _uiState.update { it.copy(isLoading = true, error = null) }
    viewModelScope.launch {
      authRepository
        .login(state.email.trim(), state.password)
        .onSuccess { _uiState.update { it.copy(isLoading = false, loginSucceeded = true) } }
        .onFailure { throwable ->
          _uiState.update { it.copy(isLoading = false, error = throwable.toLoginErrorType()) }
        }
    }
  }
}

private fun Throwable.toLoginErrorType(): LoginErrorType =
  when {
    this is ApiException && code == "invalid_credentials" -> LoginErrorType.INVALID_CREDENTIALS
    this is ApiException && code == "account_locked" -> LoginErrorType.ACCOUNT_LOCKED
    this is ApiException && code == "account_inactive" -> LoginErrorType.ACCOUNT_INACTIVE
    this is IOException -> LoginErrorType.NETWORK
    else -> LoginErrorType.GENERIC
  }
