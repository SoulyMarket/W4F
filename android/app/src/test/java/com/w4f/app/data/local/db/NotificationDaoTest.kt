package com.w4f.app.data.local.db

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import app.cash.turbine.test
import kotlinx.coroutines.test.runTest
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class NotificationDaoTest {

  private lateinit var db: AppDatabase
  private lateinit var dao: NotificationDao

  @Before
  fun setUp() {
    db =
      Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext(), AppDatabase::class.java)
        .allowMainThreadQueries()
        .build()
    dao = db.notificationDao()
  }

  @After fun tearDown() = db.close()

  private fun notification(id: String, isRead: Boolean, createdAt: Long) =
    NotificationEntity(
      id = id,
      type = "validated",
      entityType = "report",
      entityId = "r1",
      isRead = isRead,
      createdAtEpochMillis = createdAt,
      message = "تم التحقق من بلاغكم",
    )

  @Test
  fun `observeAll orders by most recent first`() = runTest {
    dao.upsertAll(listOf(notification("n1", isRead = true, createdAt = 1000), notification("n2", isRead = true, createdAt = 2000)))

    dao.observeAll().test { assertEquals(listOf("n2", "n1"), awaitItem().map { it.id }) }
  }

  @Test
  fun `unread count only counts unread rows`() = runTest {
    dao.upsertAll(
      listOf(
        notification("n1", isRead = false, createdAt = 1000),
        notification("n2", isRead = true, createdAt = 2000),
        notification("n3", isRead = false, createdAt = 3000),
      )
    )

    dao.observeUnreadCount().test { assertEquals(2, awaitItem()) }
  }

  @Test
  fun `markRead flips a single row without touching the others`() = runTest {
    dao.upsertAll(listOf(notification("n1", isRead = false, createdAt = 1000), notification("n2", isRead = false, createdAt = 2000)))

    dao.markRead("n1")

    dao.observeUnreadCount().test { assertEquals(1, awaitItem()) }
  }

  @Test
  fun `upsert replaces an existing row with the same id`() = runTest {
    dao.upsertAll(listOf(notification("n1", isRead = false, createdAt = 1000)))
    dao.upsertAll(listOf(notification("n1", isRead = true, createdAt = 1000)))

    dao.observeUnreadCount().test { assertEquals(0, awaitItem()) }
  }
}
