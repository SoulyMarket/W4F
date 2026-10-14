package com.w4f.app.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/** Enqueues section 8's outbox workers. [SyncWorker] always runs under a
 * plain "network connected" constraint (small JSON, fine over mobile data);
 * [MediaUploadWorker] defaults to Wi-Fi-only, per the "الإعدادات" setting
 * (`SyncPreferencesStore`). */
@Singleton
class SyncScheduler @Inject constructor(@ApplicationContext private val context: Context) {
  private val workManager: WorkManager
    get() = WorkManager.getInstance(context)

  fun schedulePeriodicSync() {
    val request =
      PeriodicWorkRequestBuilder<SyncWorker>(PERIODIC_INTERVAL_MINUTES, TimeUnit.MINUTES)
        .setConstraints(networkConnectedConstraints())
        .build()
    workManager.enqueueUniquePeriodicWork(
      PERIODIC_SYNC_WORK_NAME,
      ExistingPeriodicWorkPolicy.KEEP,
      request,
    )
  }

  /** On report save, and on "مزامنة الآن" once a Settings screen exists to
   * trigger it. */
  fun syncNow() {
    val request =
      OneTimeWorkRequestBuilder<SyncWorker>()
        .setConstraints(networkConnectedConstraints())
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, MIN_BACKOFF_SECONDS, TimeUnit.SECONDS)
        .build()
    workManager.enqueueUniqueWork(IMMEDIATE_SYNC_WORK_NAME, ExistingWorkPolicy.REPLACE, request)
  }

  fun enqueueMediaUpload(wifiOnly: Boolean) {
    val constraints =
      Constraints.Builder()
        .setRequiredNetworkType(if (wifiOnly) NetworkType.UNMETERED else NetworkType.CONNECTED)
        .build()
    val request =
      OneTimeWorkRequestBuilder<MediaUploadWorker>()
        .setConstraints(constraints)
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, MIN_BACKOFF_SECONDS, TimeUnit.SECONDS)
        .build()
    workManager.enqueueUniqueWork(MEDIA_UPLOAD_WORK_NAME, ExistingWorkPolicy.REPLACE, request)
  }

  private fun networkConnectedConstraints() =
    Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()

  private companion object {
    const val PERIODIC_INTERVAL_MINUTES = 15L
    const val MIN_BACKOFF_SECONDS = 30L
    const val PERIODIC_SYNC_WORK_NAME = "periodic_sync"
    const val IMMEDIATE_SYNC_WORK_NAME = "immediate_sync"
    const val MEDIA_UPLOAD_WORK_NAME = "media_upload"
  }
}
