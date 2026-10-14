package com.w4f.app.data.remote

import com.w4f.app.data.remote.dto.SyncPullResponseDto
import com.w4f.app.data.remote.dto.SyncPushRequestDto
import com.w4f.app.data.remote.dto.SyncPushResponseDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface SyncApi {
  @POST("sync/push") suspend fun push(@Body body: SyncPushRequestDto): SyncPushResponseDto

  @GET("sync/pull") suspend fun pull(@Query("since") since: String? = null): SyncPullResponseDto
}
