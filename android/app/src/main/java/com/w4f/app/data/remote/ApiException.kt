package com.w4f.app.data.remote

import com.w4f.app.data.remote.dto.ApiErrorDto
import kotlinx.serialization.json.Json
import okhttp3.ResponseBody
import retrofit2.HttpException

/** The backend's error envelope (section 5), parsed into a typed exception
 * ViewModels can match on `code` without string-parsing a message meant for
 * display. */
class ApiException(val code: String, override val message: String) : Exception(message)

fun Throwable.toApiException(json: Json): Throwable {
  if (this !is HttpException) return this
  val body: ResponseBody = response()?.errorBody() ?: return this
  return try {
    val parsed = json.decodeFromString<ApiErrorDto>(body.string())
    ApiException(parsed.error.code, parsed.error.message)
  } catch (_: Exception) {
    this
  }
}
