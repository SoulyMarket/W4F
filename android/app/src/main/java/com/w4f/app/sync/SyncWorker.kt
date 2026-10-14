package com.w4f.app.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.w4f.app.data.local.SyncPreferencesStore
import com.w4f.app.data.repository.SyncRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

/** Section 8's outbox: "pushes pending reports, uploads media..., then
 * pulls with the stored cursor." Media upload is its own worker
 * ([MediaUploadWorker]) with a stricter (Wi-Fi, by default) constraint —
 * this one only pushes report data (small JSON, fine over any connection)
 * and pulls, enqueuing the media worker once there's something registered
 * server-side to actually upload. */
@HiltWorker
class SyncWorker
@AssistedInject
constructor(
  @Assisted context: Context,
  @Assisted params: WorkerParameters,
  private val syncRepository: SyncRepository,
  private val syncScheduler: SyncScheduler,
  private val preferencesStore: SyncPreferencesStore,
) : CoroutineWorker(context, params) {

  override suspend fun doWork(): Result {
    syncRepository.pushPendingReports().onFailure {
      return Result.retry()
    }
    syncScheduler.enqueueMediaUpload(wifiOnly = preferencesStore.getWifiOnlyUpload())

    syncRepository.pull().onFailure {
      return Result.retry()
    }
    return Result.success()
  }
}
