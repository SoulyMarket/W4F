package com.w4f.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class MediaUploadUrlOutDto(
  @SerialName("media_id") val mediaId: String,
  @SerialName("upload_url") val uploadUrl: String,
  @SerialName("object_key") val objectKey: String,
  @SerialName("expires_in") val expiresIn: Int,
)

@Serializable data class MediaCompleteRequestDto(val sha256: String)

@Serializable
data class MediaOutDto(
  val id: String,
  @SerialName("report_id") val reportId: String,
  val kind: String,
  @SerialName("mime_type") val mimeType: String,
  @SerialName("size_bytes") val sizeBytes: Long,
  @SerialName("upload_status") val uploadStatus: String,
  @SerialName("download_url") val downloadUrl: String?,
)
