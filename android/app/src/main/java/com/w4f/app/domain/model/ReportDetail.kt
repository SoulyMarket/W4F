package com.w4f.app.domain.model

import java.time.Instant

data class ReportDetailMedia(
  val id: String,
  val kind: MediaKind,
  val uploadStatus: String,
  val downloadUrl: String?,
)

data class PriorityBreakdownItem(val criterion: String, val points: Double, val weight: Double, val reason: String)

data class ReportPriority(val score: Int, val breakdown: List<PriorityBreakdownItem>, val computedAt: Instant)

data class ValidationRecord(
  val id: String,
  val decision: String,
  val comment: String?,
  val proposedSolution: String?,
  val urgencyOpinion: String?,
  val createdAt: Instant,
)

data class LinkedProject(val id: String, val title: String, val status: String, val progressPercent: Int)

/** Section 8, screen 4 — "تفاصيل الملف": fetched live from `GET
 * /reports/{id}` rather than cached in Room — unlike the dossier list
 * (which must work fully offline), the detail view's whole point is
 * showing the latest server state (priority reasoning, validation
 * history, project progress), which only exists meaningfully once synced
 * anyway. */
data class ReportDetail(
  val id: String,
  val douarId: String,
  val waterSource: WaterSource,
  val problemType: ProblemType,
  val durationDays: Int,
  val interruptionFrequency: InterruptionFrequency,
  val hasAlternativeSource: Boolean,
  val alternativeDistanceKm: Double?,
  val severityReported: SeverityLevel,
  val waterQualityRisk: Boolean,
  val affectedFamilies: Int,
  val affectedPeople: Int,
  val observations: String?,
  val status: String,
  val score: Int?,
  val media: List<ReportDetailMedia>,
  val priority: ReportPriority?,
  val validations: List<ValidationRecord>,
  val project: LinkedProject?,
)
