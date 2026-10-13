package com.w4f.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable data class LoginRequestDto(val email: String, val password: String)

@Serializable
data class TokenPairDto(
  @SerialName("access_token") val accessToken: String,
  @SerialName("refresh_token") val refreshToken: String,
  @SerialName("token_type") val tokenType: String,
)

@Serializable data class RefreshRequestDto(@SerialName("refresh_token") val refreshToken: String)

@Serializable
data class TerritorySummaryDto(
  val id: String,
  @SerialName("name_ar") val nameAr: String,
  @SerialName("name_fr") val nameFr: String,
  val level: String,
)

@Serializable
data class MeResponseDto(
  val id: String,
  @SerialName("full_name") val fullName: String,
  val email: String,
  val role: String,
  @SerialName("preferred_language") val preferredLanguage: String,
  val territories: List<TerritorySummaryDto>,
)

@Serializable
data class ApiErrorDto(val error: ApiErrorDetailDto)

@Serializable data class ApiErrorDetailDto(val code: String, val message: String)
