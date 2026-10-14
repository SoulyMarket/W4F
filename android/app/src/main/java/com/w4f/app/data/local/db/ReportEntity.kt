package com.w4f.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/** The phone's own record of a report. `id` is client-generated (a random
 * UUID, assigned the moment the moqaddem starts a new report) specifically
 * so `POST /sync/push` can be idempotent — this same id is the primary key
 * on the server's `reports` table too (section 4). `syncState` is local-only
 * bookkeeping; `serverVersion`/`syncError` are filled in once a push
 * actually completes (step 2.4). */
@Entity(tableName = "reports")
data class ReportEntity(
  @PrimaryKey val id: String,
  val douarId: String,
  val waterSource: String,
  val problemType: String,
  val problemStartedOnEpochDay: Long,
  val durationDays: Int,
  val interruptionFrequency: String,
  val hasAlternativeSource: Boolean,
  val alternativeDistanceKm: Double?,
  val severityReported: String,
  val waterQualityRisk: Boolean,
  val affectedFamilies: Int,
  val affectedPeople: Int,
  val observations: String?,
  val lat: Double?,
  val lon: Double?,
  val locationAccuracyM: Float?,
  val collectedAtEpochMillis: Long,
  val syncState: String,
  val syncError: String?,
  val serverVersion: Int?,
)
