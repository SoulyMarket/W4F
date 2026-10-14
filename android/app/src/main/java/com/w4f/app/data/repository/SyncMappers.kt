package com.w4f.app.data.repository

import com.w4f.app.data.local.db.DouarEntity
import com.w4f.app.data.local.db.ReportEntity
import com.w4f.app.data.remote.dto.SyncDouarDto
import com.w4f.app.data.remote.dto.SyncMediaPushDto
import com.w4f.app.data.remote.dto.SyncReportDto
import com.w4f.app.data.remote.dto.SyncReportPushDto
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportMedia
import java.time.Instant
import java.time.LocalDate

/** `name.lowercase()` is an exact, reliable mapping to the backend's own
 * snake_case enum values (`TANK_TRUCK` -> `tank_truck`) for every enum this
 * touches — the Kotlin enums in `domain.model` were deliberately named to
 * mirror `app/models/enums.py` member-for-member (see PROGRESS.md), so no
 * lookup table is needed either direction. */
fun ReportMedia.toPushDto(): SyncMediaPushDto =
  SyncMediaPushDto(
    kind = kind.name.lowercase(),
    mimeType = mimeType,
    sizeBytes = sizeBytes,
    capturedAt = capturedAt.toString(),
  )

fun Report.toPushDto(media: List<ReportMedia>): SyncReportPushDto =
  SyncReportPushDto(
    id = id,
    douarId = douarId,
    waterSource = waterSource.name.lowercase(),
    problemType = problemType.name.lowercase(),
    problemStartedOn = problemStartedOn.toString(),
    durationDays = durationDays,
    interruptionFrequency = interruptionFrequency.name.lowercase(),
    hasAlternativeSource = hasAlternativeSource,
    alternativeDistanceKm = alternativeDistanceKm,
    severityReported = severityReported.name.lowercase(),
    waterQualityRisk = waterQualityRisk,
    affectedFamilies = affectedFamilies,
    affectedPeople = affectedPeople,
    observations = observations,
    lat = lat,
    lon = lon,
    locationAccuracyM = locationAccuracyM,
    collectedAt = collectedAt.toString(),
    media = media.map { it.toPushDto() },
  )

fun SyncDouarDto.toEntity(): DouarEntity =
  DouarEntity(id = id, nameAr = nameAr, nameFr = nameFr, communeId = communeId, lat = lat, lon = lon)

/** Materializes a report `/sync/pull` returned that this device never
 * created itself (a fresh install, or a second device on the same
 * account) — already confirmed server-side, so it starts `SYNCED`, not
 * `PENDING` (section 8: "Room is the single source of truth" means it has
 * to end up here somehow, not that this device originated it). */
fun SyncReportDto.toEntity(): ReportEntity =
  ReportEntity(
    id = id,
    douarId = douarId,
    waterSource = waterSource.uppercase(),
    problemType = problemType.uppercase(),
    problemStartedOnEpochDay = LocalDate.parse(problemStartedOn).toEpochDay(),
    durationDays = durationDays,
    interruptionFrequency = interruptionFrequency.uppercase(),
    hasAlternativeSource = hasAlternativeSource,
    alternativeDistanceKm = alternativeDistanceKm,
    severityReported = severityReported.uppercase(),
    waterQualityRisk = waterQualityRisk,
    affectedFamilies = affectedFamilies,
    affectedPeople = affectedPeople,
    observations = observations,
    lat = lat,
    lon = lon,
    locationAccuracyM = locationAccuracyM,
    collectedAtEpochMillis = Instant.parse(collectedAt).toEpochMilli(),
    syncState = "SYNCED",
    syncError = null,
    serverVersion = version,
    serverStatus = status,
    serverScore = score,
  )
