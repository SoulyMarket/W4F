package com.w4f.app.data.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface NotificationDao {
  @Insert(onConflict = OnConflictStrategy.REPLACE)
  suspend fun upsertAll(notifications: List<NotificationEntity>)

  @Query("SELECT * FROM notifications ORDER BY createdAtEpochMillis DESC")
  fun observeAll(): Flow<List<NotificationEntity>>

  @Query("SELECT COUNT(*) FROM notifications WHERE isRead = 0")
  fun observeUnreadCount(): Flow<Int>

  @Query("UPDATE notifications SET isRead = 1 WHERE id = :id") suspend fun markRead(id: String)
}
