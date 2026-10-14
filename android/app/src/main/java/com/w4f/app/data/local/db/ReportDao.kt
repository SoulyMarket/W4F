package com.w4f.app.data.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface ReportDao {
  @Insert(onConflict = OnConflictStrategy.ABORT) suspend fun insert(report: ReportEntity)

  @Update suspend fun update(report: ReportEntity)

  @Query("SELECT * FROM reports ORDER BY collectedAtEpochMillis DESC")
  fun observeAll(): Flow<List<ReportEntity>>

  @Query("SELECT * FROM reports WHERE id = :id") fun observeById(id: String): Flow<ReportEntity?>

  @Query("SELECT * FROM reports WHERE syncState = 'PENDING'")
  suspend fun getPending(): List<ReportEntity>

  @Query("UPDATE reports SET syncState = :syncState, syncError = :syncError WHERE id = :id")
  suspend fun updateSyncState(id: String, syncState: String, syncError: String?)
}
