package com.w4f.app.data.remote

import com.w4f.app.data.remote.dto.MediaCompleteRequestDto
import com.w4f.app.data.remote.dto.MediaOutDto
import com.w4f.app.data.remote.dto.MediaUploadUrlOutDto
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Path

interface MediaApi {
  @POST("media/{id}/refresh-upload-url")
  suspend fun refreshUploadUrl(@Path("id") mediaId: String): MediaUploadUrlOutDto

  @POST("media/{id}/complete")
  suspend fun complete(@Path("id") mediaId: String, @Body body: MediaCompleteRequestDto): MediaOutDto
}
