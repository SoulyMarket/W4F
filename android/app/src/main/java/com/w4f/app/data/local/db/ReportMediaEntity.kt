package com.w4f.app.data.local.db

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/** A photo/video captured for a report (section 8, "الإثباتات") before it's
 * ever uploaded — `localUri` points at the compressed file in app-private
 * storage. Uploading (step 2.4's `MediaUploadWorker`) registers this with
 * `/sync/push`'s media metadata and PUTs the bytes to the presigned URL that
 * comes back. */
@Entity(
  tableName = "report_media",
  foreignKeys =
    [
      ForeignKey(
        entity = ReportEntity::class,
        parentColumns = ["id"],
        childColumns = ["reportId"],
        onDelete = ForeignKey.CASCADE,
      )
    ],
  indices = [Index("reportId")],
)
data class ReportMediaEntity(
  @PrimaryKey val id: String,
  val reportId: String,
  val kind: String,
  val localUri: String,
  val mimeType: String,
  val sizeBytes: Long,
  val capturedAtEpochMillis: Long,
  val syncState: String,
  // Filled in once `/sync/push` registers this media item server-side —
  // the id MediaUploadWorker (step 2.4) targets for refresh-upload-url and
  // complete, distinct from this row's own client-generated `id`.
  val serverId: String? = null,
)
