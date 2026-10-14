package com.w4f.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Reference data cached from `GET /sync/pull` (step 2.4) — reads happen
 * entirely against this local cache (section 8: "Room is the single source
 * of truth"), never against the network directly. */
@Entity(tableName = "douars")
data class DouarEntity(
  @PrimaryKey val id: String,
  val nameAr: String,
  val nameFr: String,
  val communeId: String,
  val lat: Double?,
  val lon: Double?,
)
