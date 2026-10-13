package com.w4f.app

import androidx.lifecycle.ViewModel
import com.w4f.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.StateFlow

/** Whether a session already exists, decided once at process start — the
 * splash-to-first-screen decision (Login vs. Home), not re-evaluated on
 * every recomposition. */
@HiltViewModel
class RootViewModel @Inject constructor(authRepository: AuthRepository) : ViewModel() {
  val hasSession: StateFlow<Boolean> = authRepository.hasSession
}
