package com.w4f.app.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.w4f.app.data.repository.SyncRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

/** Section 8: "separate `MediaUploadWorker` (Wi-Fi constraint by default,
 * resumable/retry with backoff)" — the Wi-Fi requirement lives in this
 * worker's `Constraints` at enqueue time ([SyncScheduler]), not in the
 * repository call itself. */
@HiltWorker
class MediaUploadWorker
@AssistedInject
constructor(
  @Assisted context: Context,
  @Assisted params: WorkerParameters,
  private val syncRepository: SyncRepository,
) : CoroutineWorker(context, params) {

  override suspend fun doWork(): Result =
    syncRepository.uploadPendingMedia().fold(onSuccess = { Result.success() }, onFailure = { Result.retry() })
}
