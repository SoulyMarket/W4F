package com.w4f.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Section 8, screen 5 — "الإشعارات": cached from `/sync/pull` so the
 * notification center works offline like the rest of the app. `message`
 * is the server-rendered, already-localized string (see `SyncNotificationDto`
 * for why this isn't `type` + raw params). */
@Entity(tableName = "notifications")
data class NotificationEntity(
  @PrimaryKey val id: String,
  val type: String,
  val entityType: String,
  val entityId: String,
  val isRead: Boolean,
  val createdAtEpochMillis: Long,
  val message: String,
)
