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

  @Query("SELECT * FROM report_media WHERE reportId = :reportId ORDER BY capturedAtEpochMillis")
  suspend fun getByReportId(reportId: String): List<ReportMediaEntity>

  @Query("SELECT * FROM report_media WHERE syncState = 'PENDING' AND serverId IS NOT NULL")
  suspend fun getPendingWithServerId(): List<ReportMediaEntity>

  @Query("UPDATE report_media SET syncState = :syncState WHERE id = :id")
  suspend fun updateSyncState(id: String, syncState: String)

  @Query("UPDATE report_media SET serverId = :serverId WHERE id = :id")
  suspend fun updateServerId(id: String, serverId: String)
}
