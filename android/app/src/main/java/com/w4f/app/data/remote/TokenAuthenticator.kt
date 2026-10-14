package com.w4f.app.data.remote

import com.w4f.app.BuildConfig
import com.w4f.app.data.local.TokenStore
import com.w4f.app.data.remote.dto.RefreshRequestDto
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json
import okhttp3.Authenticator
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory

/** Handles a 401 mid-request by refreshing the session and retrying once —
 * the gap `NetworkModule`'s auth interceptor originally flagged as needing
 * "a real retry-after-refresh policy" for background sync (step 2.4), since
 * `SyncWorker`/`MediaUploadWorker` run with no user present to react to a
 * plain 401 the way the login screen does.
 *
 * Deliberately builds its own tiny Retrofit/OkHttp pair for the refresh call
 * itself rather than depending on the app's main `AuthApi` binding — that
 * binding comes from the very `OkHttpClient` this authenticator attaches to,
 * which would be a circular dependency.
 */
@Singleton
class TokenAuthenticator @Inject constructor(private val tokenStore: TokenStore, json: Json) :
  Authenticator {

  private val refreshApi: AuthApi by lazy {
    Retrofit.Builder()
      .baseUrl(BuildConfig.API_BASE_URL)
      .client(OkHttpClient.Builder().build())
      .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
      .build()
      .create(AuthApi::class.java)
  }

  private val mutex = Mutex()

  override fun authenticate(route: Route?, response: Response): Request? {
    if (priorResponseCount(response) >= MAX_RETRIES) return null

    val failedToken = response.request.header("Authorization")?.removePrefix("Bearer ")
    return runBlocking {
      mutex.withLock {
        val currentToken = tokenStore.getAccessToken()
        if (currentToken != null && currentToken != failedToken) {
          // Another request already refreshed while this one waited for the lock.
          return@withLock response.request.newBuilder().header("Authorization", "Bearer $currentToken").build()
        }

        val refreshToken = tokenStore.getRefreshToken() ?: return@withLock null
        val tokens = runCatching { refreshApi.refresh(RefreshRequestDto(refreshToken)) }.getOrNull()
        if (tokens == null) {
          // Reuse-detection revoked the family, or the token is simply
          // expired — either way there's no session left to retry with.
          tokenStore.clear()
          return@withLock null
        }

        tokenStore.saveTokens(tokens.accessToken, tokens.refreshToken)
        response.request.newBuilder().header("Authorization", "Bearer ${tokens.accessToken}").build()
      }
    }
  }

  private fun priorResponseCount(response: Response): Int {
    var count = 1
    var prior = response.priorResponse
    while (prior != null) {
      count++
      prior = prior.priorResponse
    }
    return count
  }

  private companion object {
    const val MAX_RETRIES = 2
  }
}
