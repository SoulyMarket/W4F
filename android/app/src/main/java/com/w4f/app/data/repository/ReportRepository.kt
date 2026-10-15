package com.w4f.app.data.repository

import com.w4f.app.data.local.db.ReportDao
import com.w4f.app.data.local.db.ReportMediaDao
import com.w4f.app.data.remote.ReportApi
import com.w4f.app.data.remote.toApiException
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportDetail
import com.w4f.app.domain.model.ReportMedia
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json

interface ReportRepository {
  /** Local save only (section 8: never block data entry on network) — the
   * report lands with `syncState = PENDING` and is picked up by
   * `SyncWorker` (step 2.4). */
  suspend fun saveNewReport(report: Report, media: List<ReportMedia>)

  fun observeReports(): Flow<List<Report>>

  fun observeReport(id: String): Flow<Report?>

  fun observeMedia(reportId: String): Flow<List<ReportMedia>>

  /** Section 8, screen 4 — live, not Room-backed: the detail view's whole
   * point is the latest server state (priority reasoning, validation
   * history, linked project), which only exists meaningfully once synced. */
  suspend fun fetchDetail(reportId: String): Result<ReportDetail>
}

class DefaultReportRepository
@Inject
constructor(
  private val reportDao: ReportDao,
  private val mediaDao: ReportMediaDao,
  private val reportApi: ReportApi,
  private val json: Json,
) : ReportRepository {

  override suspend fun saveNewReport(report: Report, media: List<ReportMedia>) {
    reportDao.insert(report.toEntity())
    media.forEach { mediaDao.insert(it.toEntity()) }
  }

  override fun observeReports(): Flow<List<Report>> =
    reportDao.observeAll().map { entities -> entities.map { it.toDomain() } }

  override fun observeReport(id: String): Flow<Report?> =
    reportDao.observeById(id).map { it?.toDomain() }

  override fun observeMedia(reportId: String): Flow<List<ReportMedia>> =
    mediaDao.observeByReportId(reportId).map { entities -> entities.map { it.toDomain() } }

  override suspend fun fetchDetail(reportId: String): Result<ReportDetail> =
    runCatching {
        val detail = reportApi.getReportDetail(reportId)
        val project = reportApi.getProjects(reportId).items.firstOrNull()?.toDomain()
        detail.toDomain(project)
      }
      .recoverCatching { throw it.toApiException(json) }
}
