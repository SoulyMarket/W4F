package com.w4f.app.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Section 6.12: tokens live in Keystore-backed encrypted storage, never in
 * logs. Exposes a StateFlow of "is a session present" so the UI layer (nav,
 * auto-logout) can react without polling. */
interface TokenStore {
  val hasSession: StateFlow<Boolean>

  fun saveTokens(accessToken: String, refreshToken: String)

  fun getAccessToken(): String?

  fun getRefreshToken(): String?

  fun clear()
}

@Singleton
class EncryptedTokenStore @Inject constructor(@ApplicationContext context: Context) : TokenStore {

  private val prefs: SharedPreferences by lazy {
    val masterKey = MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
    EncryptedSharedPreferences.create(
      context,
      "w4f_secure_prefs",
      masterKey,
      EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
      EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )
  }

  private val _hasSession = MutableStateFlow(false)
  override val hasSession: StateFlow<Boolean> = _hasSession.asStateFlow()

  init {
    _hasSession.value = runCatching { prefs.contains(KEY_ACCESS_TOKEN) }.getOrDefault(false)
  }

  override fun saveTokens(accessToken: String, refreshToken: String) {
    prefs
      .edit()
      .putString(KEY_ACCESS_TOKEN, accessToken)
      .putString(KEY_REFRESH_TOKEN, refreshToken)
      .apply()
    _hasSession.value = true
  }

  override fun getAccessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)

  override fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)

  override fun clear() {
    prefs.edit().clear().apply()
    _hasSession.value = false
  }

  private companion object {
    const val KEY_ACCESS_TOKEN = "access_token"
    const val KEY_REFRESH_TOKEN = "refresh_token"
  }
}
