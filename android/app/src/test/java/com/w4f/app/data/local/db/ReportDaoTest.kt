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
class ReportDaoTest {

  private lateinit var db: AppDatabase
  private lateinit var dao: ReportDao

  @Before
  fun setUp() {
    db =
      Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext(), AppDatabase::class.java)
        .allowMainThreadQueries()
        .build()
    dao = db.reportDao()
  }

  @After fun tearDown() = db.close()

  private fun report(id: String, collectedAt: Long, syncState: String = "PENDING") =
    ReportEntity(
      id = id,
      douarId = "d1",
      waterSource = "WELL",
      problemType = "NO_WATER",
      problemStartedOnEpochDay = 20000,
      durationDays = 5,
      interruptionFrequency = "DAILY",
      hasAlternativeSource = false,
      alternativeDistanceKm = null,
      severityReported = "HIGH",
      waterQualityRisk = false,
      affectedFamilies = 3,
      affectedPeople = 12,
      observations = null,
      lat = 31.0,
      lon = -7.0,
      locationAccuracyM = 5f,
      collectedAtEpochMillis = collectedAt,
      syncState = syncState,
      syncError = null,
      serverVersion = null,
    )

  @Test
  fun `observeAll orders by most recently collected first`() = runTest {
    dao.insert(report("r1", collectedAt = 1000))
    dao.insert(report("r2", collectedAt = 2000))

    dao.observeAll().test { assertEquals(listOf("r2", "r1"), awaitItem().map { it.id }) }
  }

  @Test
  fun `a newly saved report starts PENDING`() = runTest {
    dao.insert(report("r1", collectedAt = 1000))

    assertEquals(listOf("r1"), dao.getPending().map { it.id })
  }

  @Test
  fun `updateSyncState moves a report out of pending`() = runTest {
    dao.insert(report("r1", collectedAt = 1000))

    dao.updateSyncState("r1", "SYNCED", null)

    assertEquals(emptyList<String>(), dao.getPending().map { it.id })
    dao.observeById("r1").test { assertEquals("SYNCED", awaitItem()?.syncState) }
  }

  @Test
  fun `updateSyncState records a rejection reason`() = runTest {
    dao.insert(report("r1", collectedAt = 1000))

    dao.updateSyncState("r1", "REJECTED", "errors.sync_conflict")

    dao.observeById("r1").test {
      val stored = awaitItem()
      assertEquals("REJECTED", stored?.syncState)
      assertEquals("errors.sync_conflict", stored?.syncError)
    }
  }
}
