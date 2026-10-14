package com.w4f.app.data.repository

import com.w4f.app.data.local.db.DouarDao
import com.w4f.app.domain.model.Douar
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

interface DouarRepository {
  /** Section 8's "الدوار" step: searchable, pre-filtered to the moqaddem's
   * own territory. Reads only from the local cache — populated by
   * `/sync/pull` (step 2.4), never fetched directly here. */
  fun search(communeIds: List<String>, query: String): Flow<List<Douar>>
}

class DefaultDouarRepository @Inject constructor(private val dao: DouarDao) : DouarRepository {
  override fun search(communeIds: List<String>, query: String): Flow<List<Douar>> =
    dao.search(communeIds, query).map { entities -> entities.map { it.toDomain() } }
}
