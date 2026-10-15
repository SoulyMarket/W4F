package com.w4f.app.data.repository

import com.w4f.app.data.local.SyncPreferencesStore
import com.w4f.app.data.local.db.DouarDao
import com.w4f.app.data.local.db.NotificationDao
import com.w4f.app.data.local.db.ReportDao
import com.w4f.app.data.local.db.ReportEntity
import com.w4f.app.data.local.db.ReportMediaDao
import com.w4f.app.data.local.db.ReportMediaEntity
import com.w4f.app.data.media.MediaUploader
import com.w4f.app.data.remote.MediaApi
import com.w4f.app.data.remote.SyncApi
import com.w4f.app.data.remote.dto.MediaOutDto
import com.w4f.app.data.remote.dto.MediaUploadUrlOutDto
import com.w4f.app.data.remote.dto.SyncDouarDto
import com.w4f.app.data.remote.dto.SyncMediaResultDto
import com.w4f.app.data.remote.dto.SyncPullResponseDto
import com.w4f.app.data.remote.dto.SyncPushResponseDto
import com.w4f.app.data.remote.dto.SyncReportDto
import com.w4f.app.data.remote.dto.SyncReportResultDto
import java.io.File
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.argumentCaptor
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.never
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class SyncRepositoryTest {

  private val syncApi: SyncApi = mock()
  private val mediaApi: MediaApi = mock()
  private val mediaUploader: MediaUploader = mock()
  private val reportDao: ReportDao = mock()
  private val reportMediaDao: ReportMediaDao = mock()
  private val douarDao: DouarDao = mock()
  private val notificationDao: NotificationDao = mock()
  private val preferencesStore: SyncPreferencesStore = mock()

  private val repository =
    DefaultSyncRepository(
      syncApi,
      mediaApi,
      mediaUploader,
      reportDao,
      reportMediaDao,
      douarDao,
      notificationDao,
      preferencesStore,
    )

  private fun reportEntity(id: String) =
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
      collectedAtEpochMillis = 1_000_000L,
      syncState = "PENDING",
      syncError = null,
      serverVersion = null,
    )

  private fun mediaEntity(id: String, reportId: String, serverId: String? = null, syncState: String = "PENDING") =
    ReportMediaEntity(
      id = id,
      reportId = reportId,
      kind = "PHOTO",
      localUri = "/tmp/$id.jpg",
      mimeType = "image/jpeg",
      sizeBytes = 100,
      capturedAtEpochMillis = 1_000_000L,
      syncState = syncState,
      serverId = serverId,
    )

  @Test
  fun `pushPendingReports does nothing when there is nothing pending`() = runTest {
    whenever(reportDao.getPending()).thenReturn(emptyList())

    val result = repository.pushPendingReports()

    assertTrue(result.isSuccess)
    verify(syncApi, never()).push(any())
  }

  @Test
  fun `a created result marks the report synced`() = runTest {
    val entity = reportEntity("r1")
    whenever(reportDao.getPending()).thenReturn(listOf(entity))
    whenever(reportMediaDao.getByReportId("r1")).thenReturn(emptyList())
    whenever(syncApi.push(any()))
      .thenReturn(SyncPushResponseDto(results = listOf(SyncReportResultDto(id = "r1", status = "created"))))

    val result = repository.pushPendingReports()

    assertTrue(result.isSuccess)
    verify(reportDao).updateSyncState("r1", "SYNCED", null)
  }

  @Test
  fun `a rejected result marks the report rejected with its reason`() = runTest {
    val entity = reportEntity("r1")
    whenever(reportDao.getPending()).thenReturn(listOf(entity))
    whenever(reportMediaDao.getByReportId("r1")).thenReturn(emptyList())
    whenever(syncApi.push(any())).thenReturn(
      SyncPushResponseDto(
        results = listOf(SyncReportResultDto(id = "r1", status = "rejected", error = "errors.sync_conflict"))
      )
    )

    repository.pushPendingReports()

    verify(reportDao).updateSyncState("r1", "REJECTED", "errors.sync_conflict")
  }

  @Test
  fun `media results are matched back to local rows positionally`() = runTest {
    val entity = reportEntity("r1")
    val media = mediaEntity("local-a", "r1")
    whenever(reportDao.getPending()).thenReturn(listOf(entity))
    whenever(reportMediaDao.getByReportId("r1")).thenReturn(listOf(media))
    whenever(syncApi.push(any())).thenReturn(
      SyncPushResponseDto(
        results =
          listOf(
            SyncReportResultDto(
              id = "r1",
              status = "created",
              media = listOf(SyncMediaResultDto(mediaId = "server-media-1", kind = "photo", mimeType = "image/jpeg", alreadyUploaded = false)),
            )
          )
      )
    )

    repository.pushPendingReports()

    verify(reportMediaDao).updateServerId("local-a", "server-media-1")
  }

  @Test
  fun `only PENDING media is included in the push payload`() = runTest {
    val entity = reportEntity("r1")
    whenever(reportDao.getPending()).thenReturn(listOf(entity))
    whenever(reportMediaDao.getByReportId("r1"))
      .thenReturn(listOf(mediaEntity("a", "r1", syncState = "PENDING"), mediaEntity("b", "r1", syncState = "SYNCED")))
    whenever(syncApi.push(any()))
      .thenReturn(SyncPushResponseDto(results = listOf(SyncReportResultDto(id = "r1", status = "created"))))

    repository.pushPendingReports()

    val captor = argumentCaptor<com.w4f.app.data.remote.dto.SyncPushRequestDto>()
    verify(syncApi).push(captor.capture())
    assertEquals(1, captor.firstValue.reports.single().media.size)
  }

  @Test
  fun `uploading pending media completes the full upload-complete flow`() = runTest {
    val file = File.createTempFile("w4f_sync_test", ".jpg")
    file.writeBytes(byteArrayOf(1, 2, 3))
    val media = mediaEntity("local-a", "r1", serverId = "server-1").copy(localUri = file.absolutePath)
    whenever(reportMediaDao.getPendingWithServerId()).thenReturn(listOf(media))
    whenever(mediaApi.refreshUploadUrl("server-1"))
      .thenReturn(MediaUploadUrlOutDto(mediaId = "server-1", uploadUrl = "https://example/upload", objectKey = "k", expiresIn = 900))
    whenever(mediaUploader.put(eq("https://example/upload"), any(), eq("image/jpeg"))).thenReturn(true)
    whenever(mediaUploader.sha256Hex(any())).thenReturn("deadbeef")
    whenever(mediaApi.complete(eq("server-1"), any()))
      .thenReturn(MediaOutDto(id = "server-1", reportId = "r1", kind = "photo", mimeType = "image/jpeg", sizeBytes = 3, uploadStatus = "uploaded", downloadUrl = null))

    val result = repository.uploadPendingMedia()

    assertTrue(result.isSuccess)
    verify(reportMediaDao).updateSyncState("local-a", "SYNCED")
    file.delete()
  }

  @Test
  fun `a failed upload marks the media FAILED without calling complete`() = runTest {
    val file = File.createTempFile("w4f_sync_test", ".jpg")
    file.writeBytes(byteArrayOf(1, 2, 3))
    val media = mediaEntity("local-a", "r1", serverId = "server-1").copy(localUri = file.absolutePath)
    whenever(reportMediaDao.getPendingWithServerId()).thenReturn(listOf(media))
    whenever(mediaApi.refreshUploadUrl("server-1"))
      .thenReturn(MediaUploadUrlOutDto(mediaId = "server-1", uploadUrl = "https://example/upload", objectKey = "k", expiresIn = 900))
    whenever(mediaUploader.put(any(), any(), any())).thenReturn(false)

    repository.uploadPendingMedia()

    verify(reportMediaDao).updateSyncState("local-a", "FAILED")
    verify(mediaApi, never()).complete(any(), any())
    file.delete()
  }

  @Test
  fun `a missing local file is marked FAILED without contacting the server`() = runTest {
    val media = mediaEntity("local-a", "r1", serverId = "server-1").copy(localUri = "/no/such/file.jpg")
    whenever(reportMediaDao.getPendingWithServerId()).thenReturn(listOf(media))

    repository.uploadPendingMedia()

    verify(reportMediaDao).updateSyncState("local-a", "FAILED")
    verify(mediaApi, never()).refreshUploadUrl(any())
  }

  @Test
  fun `pull upserts douars, updates existing reports and inserts unseen ones`() = runTest {
    whenever(preferencesStore.getCursor()).thenReturn(null)
    whenever(reportDao.countById("existing")).thenReturn(1)
    whenever(reportDao.countById("new-one")).thenReturn(0)
    whenever(syncApi.pull(null)).thenReturn(
      SyncPullResponseDto(
        cursor = "2026-01-01T00:00:00Z",
        douars = listOf(SyncDouarDto(id = "d1", nameAr = "د", nameFr = "D", communeId = "c1", lat = 31.0, lon = -7.0, population = null, familiesCount = null)),
        reports =
          listOf(
            SyncReportDto(
              id = "existing",
              douarId = "d1",
              waterSource = "well",
              problemType = "no_water",
              problemStartedOn = "2026-01-01",
              durationDays = 5,
              interruptionFrequency = "daily",
              hasAlternativeSource = false,
              alternativeDistanceKm = null,
              severityReported = "high",
              waterQualityRisk = false,
              affectedFamilies = 3,
              affectedPeople = 12,
              observations = null,
              lat = 31.0,
              lon = -7.0,
              locationAccuracyM = 5f,
              collectedAt = "2026-01-01T00:00:00Z",
              status = "validated",
              version = 2,
              score = 70,
            ),
            SyncReportDto(
              id = "new-one",
              douarId = "d1",
              waterSource = "well",
              problemType = "no_water",
              problemStartedOn = "2026-01-01",
              durationDays = 5,
              interruptionFrequency = "daily",
              hasAlternativeSource = false,
              alternativeDistanceKm = null,
              severityReported = "high",
              waterQualityRisk = false,
              affectedFamilies = 3,
              affectedPeople = 12,
              observations = null,
              lat = 31.0,
              lon = -7.0,
              locationAccuracyM = 5f,
              collectedAt = "2026-01-01T00:00:00Z",
              status = "submitted",
              version = 1,
              score = null,
            ),
          ),
      )
    )

    val result = repository.pull()

    assertTrue(result.isSuccess)
    verify(douarDao).upsertAll(any())
    verify(reportDao).updateServerState("existing", "validated", 70, 2)
    val insertedCaptor = argumentCaptor<ReportEntity>()
    verify(reportDao).insert(insertedCaptor.capture())
    assertEquals("new-one", insertedCaptor.firstValue.id)
    verify(preferencesStore).setCursor("2026-01-01T00:00:00Z")
  }

  @Test
  fun `a push failure is surfaced as a Result failure rather than thrown`() = runTest {
    whenever(reportDao.getPending()).thenReturn(listOf(reportEntity("r1")))
    whenever(reportMediaDao.getByReportId("r1")).thenReturn(emptyList())
    whenever(syncApi.push(any())).thenThrow(RuntimeException("network down"))

    val result = repository.pushPendingReports()

    assertFalse(result.isSuccess)
  }
}
