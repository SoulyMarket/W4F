package com.w4f.app.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class ReportMediaOutDto(
  val id: String,
  val kind: String,
  @SerialName("mime_type") val mimeType: String,
  @SerialName("upload_status") val uploadStatus: String,
  @SerialName("download_url") val downloadUrl: String?,
)

/** `reason` is already localized server-side (Accept-Language) — section
 * 2.1's «لماذا هذه الأولوية؟» breakdown. `value`/`reason_params` stay as raw
 * JSON since their shape varies per criterion and nothing here needs them
 * beyond display. */
@Serializable
data class PriorityBreakdownEntryDto(
  val criterion: String,
  val value: JsonElement,
  val weight: Double,
  val points: Double,
  @SerialName("reason_key") val reasonKey: String,
  @SerialName("reason_params") val reasonParams: JsonElement,
  val reason: String,
)

@Serializable
data class PriorityOutDto(
  val score: Int,
  val breakdown: List<PriorityBreakdownEntryDto>,
  @SerialName("computed_at") val computedAt: String,
)

@Serializable
data class ValidationOutDto(
  val id: String,
  @SerialName("expert_id") val expertId: String,
  val decision: String,
  val comment: String?,
  @SerialName("proposed_solution") val proposedSolution: String?,
  @SerialName("urgency_opinion") val urgencyOpinion: String?,
  @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ReportDetailDto(
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
  val status: String,
  val version: Int,
  val score: Int?,
  val media: List<ReportMediaOutDto>,
  val priority: PriorityOutDto?,
  val validations: List<ValidationOutDto>,
)

@Serializable
data class ProjectOutDto(
  val id: String,
  @SerialName("report_id") val reportId: String,
  val title: String,
  @SerialName("solution_type") val solutionType: String,
  val status: String,
  @SerialName("progress_percent") val progressPercent: Int,
)

@Serializable data class ProjectListOutDto(val items: List<ProjectOutDto>)
