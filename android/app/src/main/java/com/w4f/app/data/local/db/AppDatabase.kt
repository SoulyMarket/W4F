package com.w4f.app.data.local.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
  entities = [DouarEntity::class, ReportEntity::class, ReportMediaEntity::class],
  version = 1,
  exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
  abstract fun douarDao(): DouarDao

  abstract fun reportDao(): ReportDao

  abstract fun reportMediaDao(): ReportMediaDao
}
