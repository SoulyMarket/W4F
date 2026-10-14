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
class DouarDaoTest {

  private lateinit var db: AppDatabase
  private lateinit var dao: DouarDao

  @Before
  fun setUp() {
    db =
      Room.inMemoryDatabaseBuilder(ApplicationProvider.getApplicationContext(), AppDatabase::class.java)
        .allowMainThreadQueries()
        .build()
    dao = db.douarDao()
  }

  @After fun tearDown() = db.close()

  private fun douar(id: String, nameAr: String, nameFr: String, communeId: String) =
    DouarEntity(id = id, nameAr = nameAr, nameFr = nameFr, communeId = communeId, lat = 31.0, lon = -7.0)

  @Test
  fun `search returns every locally cached douar when the query is blank`() = runTest {
    dao.upsertAll(
      listOf(
        douar("d1", "دوار الف", "Douar Alpha", "commune-1"),
        douar("d2", "دوار باء", "Douar Beta", "commune-2"),
      )
    )

    // No client-side territory filter — /sync/pull already only ever
    // caches douars the signed-in moqaddem can see (see DouarDao.search's
    // doc comment for the bug this replaced).
    dao.search(query = "").test {
      val result = awaitItem()
      assertEquals(listOf("d1", "d2"), result.map { it.id })
    }
  }

  @Test
  fun `search matches either the Arabic or French name`() = runTest {
    dao.upsertAll(
      listOf(
        douar("d1", "دوار الف", "Douar Alpha", "commune-1"),
        douar("d2", "دوار باء", "Douar Beta", "commune-1"),
      )
    )

    dao.search(query = "Beta").test {
      assertEquals(listOf("d2"), awaitItem().map { it.id })
    }

    dao.search(query = "الف").test {
      assertEquals(listOf("d1"), awaitItem().map { it.id })
    }
  }

  @Test
  fun `upsert replaces an existing row with the same id`() = runTest {
    dao.upsertAll(listOf(douar("d1", "دوار الف", "Douar Alpha", "commune-1")))
    dao.upsertAll(listOf(douar("d1", "دوار الف المحدث", "Douar Alpha Updated", "commune-1")))

    val stored = dao.getById("d1")
    assertEquals("Douar Alpha Updated", stored?.nameFr)
  }
}
