package com.w4f.app.domain.model

import java.time.Instant
import java.time.LocalDate

enum class WaterSource {
  NETWORK,
  WELL,
  SPRING,
  TANK_TRUCK,
  RIVER,
  OTHER;

  companion object {
    fun fromApiValue(value: String): WaterSource = valueOf(value.uppercase())
  }
}

enum class ProblemType {
  NO_WATER,
  INTERMITTENT,
  LOW_PRESSURE,
  CONTAMINATION,
  BROKEN_PUMP,
  BROKEN_PIPE,
  DRY_SOURCE,
  OTHER;

  companion object {
    fun fromApiValue(value: String): ProblemType = valueOf(value.uppercase())
  }
}

enum class InterruptionFrequency {
  PERMANENT,
  DAILY,
  WEEKLY,
  MONTHLY,
  RARE;

  companion object {
    fun fromApiValue(value: String): InterruptionFrequency = valueOf(value.uppercase())
  }
}

enum class SeverityLevel {
  LOW,
  MEDIUM,
  HIGH,
  CRITICAL;

  companion object {
    fun fromApiValue(value: String): SeverityLevel = valueOf(value.uppercase())
  }
}

enum class MediaKind {
  PHOTO,
  VIDEO,
}

/** Mirrors the phone's own sync lifecycle for a report (section 8's
 * offline-first rules) — distinct from the server's `ReportStatus`, which
 * only exists once a report has actually reached the backend. */
enum class SyncState {
  PENDING,
  SYNCING,
  SYNCED,
  FAILED,
  REJECTED,
}

data class Douar(
  val id: String,
  val nameAr: String,
  val nameFr: String,
  val communeId: String,
  val lat: Double?,
  val lon: Double?,
)

data class ReportMedia(
  val id: String,
  val reportId: String,
  val kind: MediaKind,
  val localUri: String,
  val mimeType: String,
  val sizeBytes: Long,
  val capturedAt: Instant,
  val syncState: SyncState,
)

/** A report as the phone knows it — created locally with a client-generated
 * id (section 4) so sync push is idempotent; `syncState` tracks whether it's
 * reached the server yet. Everything the moqaddem enters in the "تبليغ جديد"
 * stepper (section 8) ends up here. */
data class Report(
  val id: String,
  val douarId: String,
  val waterSource: WaterSource,
  val problemType: ProblemType,
  val problemStartedOn: LocalDate,
  val durationDays: Int,
  val interruptionFrequency: InterruptionFrequency,
  val hasAlternativeSource: Boolean,
  val alternativeDistanceKm: Double?,
  val severityReported: SeverityLevel,
  val waterQualityRisk: Boolean,
  val affectedFamilies: Int,
  val affectedPeople: Int,
  val observations: String?,
  val lat: Double?,
  val lon: Double?,
  val locationAccuracyM: Float?,
  val collectedAt: Instant,
  val syncState: SyncState,
  val syncError: String?,
  val serverStatus: String?,
  val serverScore: Int?,
)
