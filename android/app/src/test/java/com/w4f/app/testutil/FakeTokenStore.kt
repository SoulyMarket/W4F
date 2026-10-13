package com.w4f.app.testutil

import com.w4f.app.data.local.TokenStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/** In-memory TokenStore for tests — the real EncryptedTokenStore needs a
 * live Android Keystore, which isn't worth pulling Robolectric in for when
 * what's actually under test is the repository logic around it. */
class FakeTokenStore : TokenStore {
  private var accessToken: String? = null
  private var refreshToken: String? = null
  private val _hasSession = MutableStateFlow(false)
  override val hasSession: StateFlow<Boolean> = _hasSession

  override fun saveTokens(accessToken: String, refreshToken: String) {
    this.accessToken = accessToken
    this.refreshToken = refreshToken
    _hasSession.value = true
  }

  override fun getAccessToken(): String? = accessToken

  override fun getRefreshToken(): String? = refreshToken

  override fun clear() {
    accessToken = null
    refreshToken = null
    _hasSession.value = false
  }
}
