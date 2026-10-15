package com.w4f.app.data.local.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
  entities =
    [DouarEntity::class, ReportEntity::class, ReportMediaEntity::class, NotificationEntity::class],
  // v2 added ReportEntity.serverStatus/serverScore (step 2.4's pull sync);
  // v3 added NotificationEntity (step 2.5's notification center) —
  // destructive is acceptable pre-release: this is a cache/outbox, not the
  // system of record, and no real device has synced data yet.
  version = 3,
  exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
  abstract fun douarDao(): DouarDao

  abstract fun reportDao(): ReportDao

  abstract fun reportMediaDao(): ReportMediaDao

  abstract fun notificationDao(): NotificationDao
}
