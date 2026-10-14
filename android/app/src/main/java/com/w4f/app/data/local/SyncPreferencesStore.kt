package com.w4f.app.data.local

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.syncDataStore by preferencesDataStore(name = "sync_prefs")

/** The sync cursor (section 5's `/sync/pull?since=`) and the "الإعدادات"
 * sync settings (section 8, screen 7) — neither is sensitive, so plain
 * (unencrypted) DataStore is fine here, unlike the session tokens or the
 * Room passphrase. A Settings screen to edit `wifiOnlyUpload` isn't built
 * yet (not itemized in section 9's step list); the default (Wi-Fi only =
 * on) is what section 8 specifies either way. */
@Singleton
class SyncPreferencesStore @Inject constructor(@ApplicationContext private val context: Context) {
  private val cursorKey = stringPreferencesKey("last_pull_cursor")
  private val wifiOnlyUploadKey = booleanPreferencesKey("wifi_only_upload")

  suspend fun getCursor(): String? = context.syncDataStore.data.map { it[cursorKey] }.first()

  suspend fun setCursor(cursor: String) {
    context.syncDataStore.edit { it[cursorKey] = cursor }
  }

  suspend fun getWifiOnlyUpload(): Boolean =
    context.syncDataStore.data.map { it[wifiOnlyUploadKey] ?: true }.first()

  suspend fun setWifiOnlyUpload(enabled: Boolean) {
    context.syncDataStore.edit { it[wifiOnlyUploadKey] = enabled }
  }
}
