package com.w4f.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SyncMediaPushDto(
  val kind: String,
  @SerialName("mime_type") val mimeType: String,
  @SerialName("size_bytes") val sizeBytes: Long,
  @SerialName("captured_at") val capturedAt: String?,
)

@Serializable
data class SyncReportPushDto(
  val id: String,
  @SerialName("douar_id") val douarId: String,
  @SerialName("water_source") val waterSource: String,
  @SerialName("problem_type") val problemType: String,
  @SerialName("problem_started_on") val problemStartedOn: String,
  @SerialName("duration_days") val durationDays: Int,
  @SerialName("interruption_frequency") val interruptionFrequency: String,
  @SerialName("has_alternative_source") val hasAlternativeSource: Boolean,
  @SerialName("alternative_distance_km") val alternativeDistanceKm: Double?,
  @SerialName("severity_reported") val severityReported: String,
  @SerialName("water_quality_risk") val waterQualityRisk: Boolean,
  @SerialName("affected_families") val affectedFamilies: Int,
  @SerialName("affected_people") val affectedPeople: Int,
  val observations: String?,
  val lat: Double?,
  val lon: Double?,
  @SerialName("location_accuracy_m") val locationAccuracyM: Float?,
  @SerialName("collected_at") val collectedAt: String,
  val media: List<SyncMediaPushDto> = emptyList(),
)

@Serializable data class SyncPushRequestDto(val reports: List<SyncReportPushDto>)

@Serializable
data class SyncMediaResultDto(
  @SerialName("media_id") val mediaId: String,
  val kind: String,
  @SerialName("mime_type") val mimeType: String,
  @SerialName("already_uploaded") val alreadyUploaded: Boolean,
  @SerialName("upload_url") val uploadUrl: String? = null,
  @SerialName("object_key") val objectKey: String? = null,
  @SerialName("expires_in") val expiresIn: Int? = null,
)

@Serializable
data class SyncReportResultDto(
  val id: String,
  val status: String,
  val error: String? = null,
  val version: Int? = null,
  val media: List<SyncMediaResultDto> = emptyList(),
)

@Serializable data class SyncPushResponseDto(val results: List<SyncReportResultDto>)

@Serializable
data class SyncDouarDto(
  val id: String,
  @SerialName("name_ar") val nameAr: String,
  @SerialName("name_fr") val nameFr: String,
  @SerialName("commune_id") val communeId: String,
  val lat: Double?,
  val lon: Double?,
  val population: Int?,
  @SerialName("families_count") val familiesCount: Int?,
)

/** Mirrors the backend's `ReportOut` (section 5) — the shape `/sync/pull`
 * reuses for each of the moqaddem's own reports. Full field set rather than
 * a thin status/score-only DTO so a fresh install (or a second device on
 * the same account) can materialize reports it never created locally,
 * not just refresh ones it already has (section 8: "Room is the single
 * source of truth" — it has to end up with everything eventually). */
@Serializable
data class SyncReportDto(
  val id: String,
  @SerialName("douar_id") val douarId: String,
  @SerialName("water_source") val waterSource: String,
  @SerialName("problem_type") val problemType: String,
  @SerialName("problem_started_on") val problemStartedOn: String,
  @SerialName("duration_days") val durationDays: Int,
  @SerialName("interruption_frequency") val interruptionFrequency: String,
  @SerialName("has_alternative_source") val hasAlternativeSource: Boolean,
  @SerialName("alternative_distance_km") val alternativeDistanceKm: Double?,
  @SerialName("severity_reported") val severityReported: String,
  @SerialName("water_quality_risk") val waterQualityRisk: Boolean,
  @SerialName("affected_families") val affectedFamilies: Int,
  @SerialName("affected_people") val affectedPeople: Int,
  val observations: String?,
  val lat: Double?,
  val lon: Double?,
  @SerialName("location_accuracy_m") val locationAccuracyM: Float?,
  @SerialName("collected_at") val collectedAt: String,
  val status: String,
  val version: Int,
  val score: Int?,
)

@Serializable data class SyncPullResponseDto(
  val cursor: String,
  val douars: List<SyncDouarDto>,
  val reports: List<SyncReportDto>,
)
