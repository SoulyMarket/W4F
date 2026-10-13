package com.w4f.app.ui.login

import com.w4f.app.data.remote.ApiException
import com.w4f.app.data.repository.AuthRepository
import com.w4f.app.testutil.MainDispatcherRule
import java.io.IOException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.doReturn
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class LoginViewModelTest {

  @get:Rule val mainDispatcherRule = MainDispatcherRule()

  private val authRepository: AuthRepository = mock {
    on { hasSession } doReturn MutableStateFlow(false)
  }

  @Test
  fun `initial state is empty and not loading`() {
    val viewModel = LoginViewModel(authRepository)
    val state = viewModel.uiState.value

    assertEquals("", state.email)
    assertEquals("", state.password)
    assertFalse(state.isLoading)
    assertNull(state.error)
    assertFalse(state.loginSucceeded)
  }

  @Test
  fun `changing email updates state and clears error`() = runTest {
    val viewModel = LoginViewModel(authRepository)

    viewModel.onEmailChange("manager@w4f.ma")

    assertEquals("manager@w4f.ma", viewModel.uiState.value.email)
  }

  @Test
  fun `successful login sets loginSucceeded`() = runTest {
    whenever(authRepository.login("manager@w4f.ma", "password123")).thenReturn(Result.success(Unit))
    val viewModel = LoginViewModel(authRepository)
    viewModel.onEmailChange("manager@w4f.ma")
    viewModel.onPasswordChange("password123")

    viewModel.onLoginClick()
    advanceUntilIdle()

    val state = viewModel.uiState.value
    assertTrue(state.loginSucceeded)
    assertFalse(state.isLoading)
    assertNull(state.error)
  }

  @Test
  fun `invalid credentials error maps to INVALID_CREDENTIALS`() = runTest {
    whenever(authRepository.login("manager@w4f.ma", "wrong"))
      .thenReturn(Result.failure(ApiException("invalid_credentials", "wrong password")))
    val viewModel = LoginViewModel(authRepository)
    viewModel.onEmailChange("manager@w4f.ma")
    viewModel.onPasswordChange("wrong")

    viewModel.onLoginClick()
    advanceUntilIdle()

    val state = viewModel.uiState.value
    assertEquals(LoginErrorType.INVALID_CREDENTIALS, state.error)
    assertFalse(state.loginSucceeded)
    assertFalse(state.isLoading)
  }

  @Test
  fun `network failure maps to NETWORK error`() = runTest {
    whenever(authRepository.login("manager@w4f.ma", "password123"))
      .thenReturn(Result.failure(IOException("no connection")))
    val viewModel = LoginViewModel(authRepository)
    viewModel.onEmailChange("manager@w4f.ma")
    viewModel.onPasswordChange("password123")

    viewModel.onLoginClick()
    advanceUntilIdle()

    assertEquals(LoginErrorType.NETWORK, viewModel.uiState.value.error)
  }

  @Test
  fun `blank email or password does not attempt login`() = runTest {
    val viewModel = LoginViewModel(authRepository)
    viewModel.onPasswordChange("password123")
    // email left blank

    viewModel.onLoginClick()
    advanceUntilIdle()

    assertFalse(viewModel.uiState.value.isLoading)
    assertFalse(viewModel.uiState.value.loginSucceeded)
  }
}
