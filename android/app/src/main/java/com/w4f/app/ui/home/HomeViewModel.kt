package com.w4f.app.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.w4f.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class HomeUiState(val fullName: String? = null, val loggedOut: Boolean = false)

@HiltViewModel
class HomeViewModel @Inject constructor(private val authRepository: AuthRepository) : ViewModel() {

  private val _uiState = MutableStateFlow(HomeUiState())
  val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

  init {
    viewModelScope.launch {
      authRepository.currentUser().onSuccess { user ->
        _uiState.update { it.copy(fullName = user.fullName) }
      }
    }
  }

  fun onLogoutClick() {
    viewModelScope.launch {
      authRepository.logout()
      _uiState.update { it.copy(loggedOut = true) }
    }
  }
}
