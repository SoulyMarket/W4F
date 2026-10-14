package com.w4f.app.data.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface ReportMediaDao {
  @Insert(onConflict = OnConflictStrategy.ABORT) suspend fun insert(media: ReportMediaEntity)

  @Query("SELECT * FROM report_media WHERE reportId = :reportId ORDER BY capturedAtEpochMillis")
  fun observeByReportId(reportId: String): Flow<List<ReportMediaEntity>>
}
