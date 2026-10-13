package com.w4f.app.data.remote

import com.w4f.app.data.remote.dto.LoginRequestDto
import com.w4f.app.data.remote.dto.MeResponseDto
import com.w4f.app.data.remote.dto.RefreshRequestDto
import com.w4f.app.data.remote.dto.TokenPairDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApi {
  @POST("auth/login") suspend fun login(@Body body: LoginRequestDto): TokenPairDto

  @POST("auth/refresh") suspend fun refresh(@Body body: RefreshRequestDto): TokenPairDto

  @POST("auth/logout") suspend fun logout(@Body body: RefreshRequestDto)

  @GET("auth/me") suspend fun me(): MeResponseDto
}
