package com.w4f.app.data.repository

import com.w4f.app.data.local.db.ReportDao
import com.w4f.app.data.local.db.ReportMediaDao
import com.w4f.app.domain.model.Report
import com.w4f.app.domain.model.ReportMedia
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

interface ReportRepository {
  /** Local save only (section 8: never block data entry on network) — the
   * report lands with `syncState = PENDING` and is picked up by
   * `SyncWorker` (step 2.4). */
  suspend fun saveNewReport(report: Report, media: List<ReportMedia>)

  fun observeReports(): Flow<List<Report>>

  fun observeReport(id: String): Flow<Report?>

  fun observeMedia(reportId: String): Flow<List<ReportMedia>>
}

class DefaultReportRepository
@Inject
constructor(private val reportDao: ReportDao, private val mediaDao: ReportMediaDao) :
  ReportRepository {

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
}
