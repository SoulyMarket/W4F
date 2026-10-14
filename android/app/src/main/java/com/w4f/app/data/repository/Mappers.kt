package com.w4f.app.data.repository

import com.w4f.app.data.local.db.DouarEntity
import com.w4f.app.data.local.db.ReportEntity
import com.w4f.app.data.local.db.ReportMediaEntity
import com.w4f.app.domain.model.Douar
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.MediaKind
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportMedia
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.SyncState
import com.w4f.app.domain.model.WaterSource
import java.time.Instant
import java.time.LocalDate

fun DouarEntity.toDomain(): Douar = Douar(id, nameAr, nameFr, communeId, lat, lon)

fun Report.toEntity(): ReportEntity =
  ReportEntity(
    id = id,
    douarId = douarId,
    waterSource = waterSource.name,
    problemType = problemType.name,
    problemStartedOnEpochDay = problemStartedOn.toEpochDay(),
    durationDays = durationDays,
    interruptionFrequency = interruptionFrequency.name,
    hasAlternativeSource = hasAlternativeSource,
    alternativeDistanceKm = alternativeDistanceKm,
    severityReported = severityReported.name,
    waterQualityRisk = waterQualityRisk,
    affectedFamilies = affectedFamilies,
    affectedPeople = affectedPeople,
    observations = observations,
    lat = lat,
    lon = lon,
    locationAccuracyM = locationAccuracyM,
    collectedAtEpochMillis = collectedAt.toEpochMilli(),
    syncState = syncState.name,
    syncError = syncError,
    serverVersion = null,
  )

fun ReportEntity.toDomain(): Report =
  Report(
    id = id,
    douarId = douarId,
    waterSource = WaterSource.valueOf(waterSource),
    problemType = ProblemType.valueOf(problemType),
    problemStartedOn = LocalDate.ofEpochDay(problemStartedOnEpochDay),
    durationDays = durationDays,
    interruptionFrequency = InterruptionFrequency.valueOf(interruptionFrequency),
    hasAlternativeSource = hasAlternativeSource,
    alternativeDistanceKm = alternativeDistanceKm,
    severityReported = SeverityLevel.valueOf(severityReported),
    waterQualityRisk = waterQualityRisk,
    affectedFamilies = affectedFamilies,
    affectedPeople = affectedPeople,
    observations = observations,
    lat = lat,
    lon = lon,
    locationAccuracyM = locationAccuracyM,
    collectedAt = Instant.ofEpochMilli(collectedAtEpochMillis),
    syncState = SyncState.valueOf(syncState),
    syncError = syncError,
  )

fun ReportMedia.toEntity(): ReportMediaEntity =
  ReportMediaEntity(
    id = id,
    reportId = reportId,
    kind = kind.name,
    localUri = localUri,
    mimeType = mimeType,
    sizeBytes = sizeBytes,
    capturedAtEpochMillis = capturedAt.toEpochMilli(),
    syncState = syncState.name,
  )

fun ReportMediaEntity.toDomain(): ReportMedia =
  ReportMedia(
    id = id,
    reportId = reportId,
    kind = MediaKind.valueOf(kind),
    localUri = localUri,
    mimeType = mimeType,
    sizeBytes = sizeBytes,
    capturedAt = Instant.ofEpochMilli(capturedAtEpochMillis),
    syncState = SyncState.valueOf(syncState),
  )
