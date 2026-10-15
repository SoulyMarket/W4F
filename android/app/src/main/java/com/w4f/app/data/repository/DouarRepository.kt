package com.w4f.app.data.repository

import com.w4f.app.data.local.db.DouarDao
import com.w4f.app.domain.model.Douar
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

interface DouarRepository {
  /** Section 8's "الدوار" step: searchable, scoped to the moqaddem's own
   * territory by construction — `/sync/pull` only ever returns douars the
   * signed-in moqaddem is allowed to see (server-side province→commune
   * resolution), so the local cache never needs a second, client-side
   * territory filter on top. */
  fun search(query: String): Flow<List<Douar>>

  /** For display-only lookups (e.g. the dossier detail screen resolving a
   * report's `douarId` to a name) where a one-shot read is enough. */
  suspend fun getById(id: String): Douar?
}

class DefaultDouarRepository @Inject constructor(private val dao: DouarDao) : DouarRepository {
  override fun search(query: String): Flow<List<Douar>> =
    dao.search(query).map { entities -> entities.map { it.toDomain() } }

  override suspend fun getById(id: String): Douar? = dao.getById(id)?.toDomain()
}
