package com.w4f.app.data.repository

import com.w4f.app.data.remote.dto.ProjectOutDto
import com.w4f.app.data.remote.dto.ReportDetailDto
import com.w4f.app.domain.model.InterruptionFrequency
import com.w4f.app.domain.model.LinkedProject
import com.w4f.app.domain.model.MediaKind
import com.w4f.app.domain.model.PriorityBreakdownItem
import com.w4f.app.domain.model.ProblemType
import com.w4f.app.domain.model.ReportDetail
import com.w4f.app.domain.model.ReportDetailMedia
import com.w4f.app.domain.model.ReportPriority
import com.w4f.app.domain.model.SeverityLevel
import com.w4f.app.domain.model.ValidationRecord
import com.w4f.app.domain.model.WaterSource
import java.time.Instant

fun ReportDetailDto.toDomain(project: LinkedProject?): ReportDetail =
  ReportDetail(
    id = id,
    douarId = douarId,
    waterSource = WaterSource.valueOf(waterSource.uppercase()),
    problemType = ProblemType.valueOf(problemType.uppercase()),
    durationDays = durationDays,
    interruptionFrequency = InterruptionFrequency.valueOf(interruptionFrequency.uppercase()),
    hasAlternativeSource = hasAlternativeSource,
    alternativeDistanceKm = alternativeDistanceKm,
    severityReported = SeverityLevel.valueOf(severityReported.uppercase()),
    waterQualityRisk = waterQualityRisk,
    affectedFamilies = affectedFamilies,
    affectedPeople = affectedPeople,
    observations = observations,
    status = status,
    score = score,
    media =
      media.map {
        ReportDetailMedia(
          id = it.id,
          kind = MediaKind.valueOf(it.kind.uppercase()),
          uploadStatus = it.uploadStatus,
          downloadUrl = it.downloadUrl,
        )
      },
    priority =
      priority?.let { p ->
        ReportPriority(
          score = p.score,
          breakdown =
            p.breakdown.map { PriorityBreakdownItem(it.criterion, it.points, it.weight, it.reason) },
          computedAt = Instant.parse(p.computedAt),
        )
      },
    validations =
      validations.map {
        ValidationRecord(
          id = it.id,
          decision = it.decision,
          comment = it.comment,
          proposedSolution = it.proposedSolution,
          urgencyOpinion = it.urgencyOpinion,
          createdAt = Instant.parse(it.createdAt),
        )
      },
    project = project,
  )

fun ProjectOutDto.toDomain(): LinkedProject =
  LinkedProject(id = id, title = title, status = status, progressPercent = progressPercent)
