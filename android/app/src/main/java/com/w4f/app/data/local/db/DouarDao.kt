package com.w4f.app.data.local.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DouarDao {
  @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun upsertAll(douars: List<DouarEntity>)

  /** Pre-filtered to the moqaddem's territory (section 8, "الدوار" step) —
   * `communeIds` is the caller's accessible set, resolved the same way the
   * backend resolves it server-side. Matches either the Arabic or French
   * name, since the moqaddem may type either (section 8). */
  @Query(
    "SELECT * FROM douars WHERE communeId IN (:communeIds) " +
      "AND (nameAr LIKE '%' || :query || '%' OR nameFr LIKE '%' || :query || '%') " +
      "ORDER BY nameAr"
  )
  fun search(communeIds: List<String>, query: String): Flow<List<DouarEntity>>

  @Query("SELECT * FROM douars WHERE id = :id") suspend fun getById(id: String): DouarEntity?
}
