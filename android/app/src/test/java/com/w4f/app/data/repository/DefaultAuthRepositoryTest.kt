package com.w4f.app.data.repository

import com.w4f.app.data.remote.ApiException
import com.w4f.app.data.remote.AuthApi
import com.w4f.app.data.remote.dto.LoginRequestDto
import com.w4f.app.data.remote.dto.MeResponseDto
import com.w4f.app.data.remote.dto.RefreshRequestDto
import com.w4f.app.data.remote.dto.TerritorySummaryDto
import com.w4f.app.data.remote.dto.TokenPairDto
import com.w4f.app.testutil.FakeTokenStore
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import retrofit2.HttpException
import retrofit2.Response

class DefaultAuthRepositoryTest {

  private val api: AuthApi = mock()
  private val tokenStore = FakeTokenStore()
  private val json = Json { ignoreUnknownKeys = true }
  private lateinit var repository: DefaultAuthRepository

  @Before
  fun setUp() {
    repository = DefaultAuthRepository(api, tokenStore, json)
  }

  @Test
  fun `login saves tokens on success`() = runTest {
    whenever(api.login(LoginRequestDto("manager@w4f.ma", "pass1234")))
      .thenReturn(TokenPairDto("access-1", "refresh-1", "bearer"))

    val result = repository.login("manager@w4f.ma", "pass1234")

    assertTrue(result.isSuccess)
    assertEquals("access-1", tokenStore.getAccessToken())
    assertEquals("refresh-1", tokenStore.getRefreshToken())
    assertTrue(tokenStore.hasSession.value)
  }

  @Test
  fun `login wraps a 401 HttpException into ApiException with the backend's code and message`() =
    runTest {
      val errorJson =
        """{"error": {"code": "invalid_credentials", "message": "بيانات خاطئة"}}"""
      val httpException =
        HttpException(
          Response.error<TokenPairDto>(401, errorJson.toResponseBody("application/json".toMediaType()))
        )
      whenever(api.login(LoginRequestDto("manager@w4f.ma", "wrong"))).thenAnswer { throw httpException }

      val result = repository.login("manager@w4f.ma", "wrong")

      assertTrue(result.isFailure)
      val exception = result.exceptionOrNull()
      assertTrue(exception is ApiException)
      assertEquals("invalid_credentials", (exception as ApiException).code)
      assertFalse(tokenStore.hasSession.value)
    }

  @Test
  fun `logout calls the api and always clears local tokens even if the call fails`() = runTest {
    tokenStore.saveTokens("access-1", "refresh-1")
    whenever(api.logout(RefreshRequestDto("refresh-1"))).thenAnswer { throw RuntimeException("network down") }

    repository.logout()

    verify(api).logout(RefreshRequestDto("refresh-1"))
    assertFalse(tokenStore.hasSession.value)
  }

  @Test
  fun `logout with no stored refresh token still clears local session without calling the api`() =
    runTest {
      repository.logout()

      assertFalse(tokenStore.hasSession.value)
    }

  @Test
  fun `currentUser maps the DTO to the domain model`() = runTest {
    whenever(api.me())
      .thenReturn(
        MeResponseDto(
          id = "user-1",
          fullName = "Fatima Zahra",
          email = "fatima@w4f.ma",
          role = "expert",
          preferredLanguage = "ar",
          territories = listOf(TerritorySummaryDto("t-1", "الحوز", "Al Haouz", "province")),
        )
      )

    val result = repository.currentUser()

    assertTrue(result.isSuccess)
    val user = result.getOrThrow()
    assertEquals("user-1", user.id)
    assertEquals("Fatima Zahra", user.fullName)
    assertEquals(1, user.territories.size)
    assertEquals("Al Haouz", user.territories[0].nameFr)
  }
}
