package com.w4f.app.data.media

import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

/** Puts bytes straight to a presigned S3/MinIO URL — deliberately a plain
 * `OkHttpClient` with none of the app's own interceptors (no bearer token
 * attached: a presigned URL authenticates itself via its signed query
 * string, and MediaUploadWorker's URLs always come from
 * `/media/{id}/refresh-upload-url` right before use, so they're fresh). */
@Singleton
class MediaUploader @Inject constructor() {
  private val client = OkHttpClient()

  suspend fun put(uploadUrl: String, bytes: ByteArray, contentType: String): Boolean =
    withContext(Dispatchers.IO) {
      runCatching {
          val request =
            Request.Builder().url(uploadUrl).put(bytes.toRequestBody(contentType.toMediaType())).build()
          client.newCall(request).execute().use { it.isSuccessful }
        }
        .getOrDefault(false)
    }

  fun sha256Hex(bytes: ByteArray): String =
    MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
}
