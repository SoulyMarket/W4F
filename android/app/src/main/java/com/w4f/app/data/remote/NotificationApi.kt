package com.w4f.app.data.remote

import retrofit2.http.POST
import retrofit2.http.Path

interface NotificationApi {
  @POST("notifications/{id}/read") suspend fun markRead(@Path("id") notificationId: String)
}
