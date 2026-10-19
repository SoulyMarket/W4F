package com.w4f.app

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import com.w4f.app.sync.SyncScheduler
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class W4FApplication : Application(), Configuration.Provider {

  @Inject lateinit var workerFactory: HiltWorkerFactory
  @Inject lateinit var syncScheduler: SyncScheduler

  override val workManagerConfiguration: Configuration
    get() = Configuration.Builder().setWorkerFactory(workerFactory).build()

  override fun onCreate() {
    super.onCreate()
    // MapLibre.getInstance() is NOT called here on purpose: it loads a
    // native library that doesn't exist in the Robolectric/JVM unit test
    // environment, and Robolectric instantiates this real Application for
    // every Context-based test (DouarDaoTest, NotificationDaoTest, etc.) —
    // confirmed on this exact change (13 unrelated tests failed with
    // UnsatisfiedLinkError on MapLibre native classes until this was
    // moved into the map screen itself, step 2.5's map, which never runs
    // under Robolectric). See `ui/map/MapScreen.kt`.
    syncScheduler.schedulePeriodicSync()
  }
}
