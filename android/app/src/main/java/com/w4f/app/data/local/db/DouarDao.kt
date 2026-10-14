package com.w4f.app.data.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DouarDao {
  @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun upsertAll(douars: List<DouarEntity>)

  /** Section 8, "الدوار" step: searchable, pre-filtered to the moqaddem's
   * territory — but that filtering already happened server-side in
   * `/sync/pull` (province→commune descendant resolution lives there, see
   * the backend's `territory_scope.py`), so every row that ever reaches
   * this table already belongs to the signed-in moqaddem. Re-filtering
   * here by a client-resolved commune id was a real, confirmed-on-device
   * bug: a province-level assignment (the seeded moqaddem's own territory)
   * never matched a douar's commune-level id, so results were silently
   * empty even though the data was there. Matches either the Arabic or
   * French name, since the moqaddem may type either. */
  @Query(
    "SELECT * FROM douars WHERE nameAr LIKE '%' || :query || '%' OR nameFr LIKE '%' || :query || '%' " +
      "ORDER BY nameAr"
  )
  fun search(query: String): Flow<List<DouarEntity>>

  @Query("SELECT * FROM douars WHERE id = :id") suspend fun getById(id: String): DouarEntity?
}
