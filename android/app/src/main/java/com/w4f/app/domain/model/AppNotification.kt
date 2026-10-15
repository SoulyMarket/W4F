package com.w4f.app.domain.model

import java.time.Instant

/** Section 8, screen 5 — "الإشعارات". `message` is pre-localized by the
 * backend (see `SyncNotificationDto`'s doc comment). */
data class AppNotification(
  val id: String,
  val type: String,
  val entityType: String,
  val entityId: String,
  val isRead: Boolean,
  val createdAt: Instant,
  val message: String,
)
