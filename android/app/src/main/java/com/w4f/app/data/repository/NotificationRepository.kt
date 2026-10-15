package com.w4f.app.data.repository

import com.w4f.app.data.local.db.NotificationDao
import com.w4f.app.data.local.db.NotificationEntity
import com.w4f.app.data.remote.NotificationApi
import com.w4f.app.domain.model.AppNotification
import java.time.Instant
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private fun NotificationEntity.toDomain(): AppNotification =
  AppNotification(
    id = id,
    type = type,
    entityType = entityType,
    entityId = entityId,
    isRead = isRead,
    createdAt = Instant.ofEpochMilli(createdAtEpochMillis),
    message = message,
  )

interface NotificationRepository {
  fun observeAll(): Flow<List<AppNotification>>

  fun observeUnreadCount(): Flow<Int>

  /** Marks the row read locally first (instant feedback, works offline),
   * then tells the server — best-effort: if the network call fails there's
   * no retry queue for this one action (unlike reports), since the next
   * successful `/sync/pull` reconciles it from the server's own
   * authoritative `is_read` anyway. */
  suspend fun markRead(id: String)
}

class DefaultNotificationRepository
@Inject
constructor(private val dao: NotificationDao, private val api: NotificationApi) :
  NotificationRepository {

  override fun observeAll(): Flow<List<AppNotification>> =
    dao.observeAll().map { entities -> entities.map { it.toDomain() } }

  override fun observeUnreadCount(): Flow<Int> = dao.observeUnreadCount()

  override suspend fun markRead(id: String) {
    dao.markRead(id)
    runCatching { api.markRead(id) }
  }
}
