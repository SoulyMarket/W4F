package com.w4f.app.data.repository

import com.w4f.app.data.local.SyncPreferencesStore
import com.w4f.app.data.local.db.DouarDao
import com.w4f.app.data.local.db.ReportDao
import com.w4f.app.data.local.db.ReportMediaDao
import com.w4f.app.data.media.MediaUploader
import com.w4f.app.data.remote.MediaApi
import com.w4f.app.data.remote.SyncApi
import com.w4f.app.data.remote.dto.MediaCompleteRequestDto
import com.w4f.app.data.remote.dto.SyncPushRequestDto
import java.io.File
import javax.inject.Inject

private val SYNCED_PUSH_STATUSES = setOf("created", "updated", "unchanged")

interface SyncRepository {
  /** Pushes every locally `PENDING` report (section 8's outbox) in one
   * batch call, idempotent on retry. */
  suspend fun pushPendingReports(): Result<Unit>

  /** Uploads every captured media item whose report has already been
   * registered server-side. Never run with a non-Wi-Fi constraint unless
   * the caller (WorkManager) was explicitly configured to allow metered
   * networks — this function itself doesn't check connection type. */
  suspend fun uploadPendingMedia(): Result<Unit>

  /** Pulls everything changed in the moqaddem's territory since the
   * stored cursor, then advances it. */
  suspend fun pull(): Result<Unit>
}

class DefaultSyncRepository
@Inject
constructor(
  private val syncApi: SyncApi,
  private val mediaApi: MediaApi,
  private val mediaUploader: MediaUploader,
  private val reportDao: ReportDao,
  private val reportMediaDao: ReportMediaDao,
  private val douarDao: DouarDao,
  private val preferencesStore: SyncPreferencesStore,
) : SyncRepository {

  override suspend fun pushPendingReports(): Result<Unit> = runCatching {
    val pendingReports = reportDao.getPending()
    if (pendingReports.isEmpty()) return@runCatching

    val pendingMediaByReport =
      pendingReports.associate { report ->
        report.id to reportMediaDao.getByReportId(report.id).filter { it.syncState == "PENDING" }
      }
    val requestDtos =
      pendingReports.map { report ->
        report.toDomain().toPushDto(pendingMediaByReport.getValue(report.id).map { it.toDomain() })
      }

    // Response items and each report's media results come back in the
    // same order the request sent them — the backend has no client-facing
    // media id to echo, so this positional correspondence is how a result
    // is matched back to the local row it came from (see PROGRESS.md).
    val response = syncApi.push(SyncPushRequestDto(reports = requestDtos))

    response.results.forEach { result ->
      val newSyncState = if (result.status in SYNCED_PUSH_STATUSES) "SYNCED" else "REJECTED"
      reportDao.updateSyncState(result.id, newSyncState, result.error)

      val localMedia = pendingMediaByReport[result.id].orEmpty()
      localMedia.zip(result.media).forEach { (local, remote) ->
        reportMediaDao.updateServerId(local.id, remote.mediaId)
      }
    }
  }

  override suspend fun uploadPendingMedia(): Result<Unit> = runCatching {
    val pending = reportMediaDao.getPendingWithServerId()
    for (media in pending) {
      val serverId = media.serverId ?: continue
      val file = File(media.localUri)
      if (!file.exists()) {
        reportMediaDao.updateSyncState(media.id, "FAILED")
        continue
      }

      val fresh = runCatching { mediaApi.refreshUploadUrl(serverId) }.getOrNull()
      if (fresh == null) {
        reportMediaDao.updateSyncState(media.id, "FAILED")
        continue
      }

      val bytes = file.readBytes()
      val uploaded = mediaUploader.put(fresh.uploadUrl, bytes, media.mimeType)
      if (!uploaded) {
        reportMediaDao.updateSyncState(media.id, "FAILED")
        continue
      }

      val sha256 = mediaUploader.sha256Hex(bytes)
      runCatching { mediaApi.complete(serverId, MediaCompleteRequestDto(sha256)) }
        .onSuccess { reportMediaDao.updateSyncState(media.id, "SYNCED") }
        .onFailure { reportMediaDao.updateSyncState(media.id, "FAILED") }
    }
  }

  override suspend fun pull(): Result<Unit> = runCatching {
    val since = preferencesStore.getCursor()
    val response = syncApi.pull(since)

    douarDao.upsertAll(response.douars.map { it.toEntity() })

    response.reports.forEach { dto ->
      if (reportDao.countById(dto.id) > 0) {
        reportDao.updateServerState(dto.id, dto.status, dto.score, dto.version)
      } else {
        reportDao.insert(dto.toEntity())
      }
    }

    preferencesStore.setCursor(response.cursor)
  }
}
