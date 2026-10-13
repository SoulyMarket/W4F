package com.w4f.app.data.repository

import com.w4f.app.data.local.TokenStore
import com.w4f.app.data.remote.AuthApi
import com.w4f.app.data.remote.dto.LoginRequestDto
import com.w4f.app.data.remote.dto.MeResponseDto
import com.w4f.app.data.remote.dto.RefreshRequestDto
import com.w4f.app.data.remote.toApiException
import com.w4f.app.domain.model.AppLanguage
import com.w4f.app.domain.model.Territory
import com.w4f.app.domain.model.User
import com.w4f.app.domain.model.UserRole
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.StateFlow
import kotlinx.serialization.json.Json

interface AuthRepository {
  val hasSession: StateFlow<Boolean>

  suspend fun login(email: String, password: String): Result<Unit>

  suspend fun logout()

  suspend fun currentUser(): Result<User>
}

@Singleton
class DefaultAuthRepository
@Inject
constructor(private val api: AuthApi, private val tokenStore: TokenStore, private val json: Json) :
  AuthRepository {

  override val hasSession: StateFlow<Boolean> = tokenStore.hasSession

  override suspend fun login(email: String, password: String): Result<Unit> =
    runCatching {
        val tokens = api.login(LoginRequestDto(email = email, password = password))
        tokenStore.saveTokens(tokens.accessToken, tokens.refreshToken)
      }
      .recoverCatching { throw it.toApiException(json) }

  override suspend fun logout() {
    val refreshToken = tokenStore.getRefreshToken()
    if (refreshToken != null) {
      runCatching { api.logout(RefreshRequestDto(refreshToken)) }
    }
    tokenStore.clear()
  }

  override suspend fun currentUser(): Result<User> =
    runCatching { api.me().toDomain() }.recoverCatching { throw it.toApiException(json) }
}

private fun MeResponseDto.toDomain(): User =
  User(
    id = id,
    fullName = fullName,
    email = email,
    role = UserRole.fromApiValue(role),
    preferredLanguage = AppLanguage.fromApiValue(preferredLanguage),
    territories =
      territories.map { Territory(id = it.id, nameAr = it.nameAr, nameFr = it.nameFr, level = it.level) },
  )
