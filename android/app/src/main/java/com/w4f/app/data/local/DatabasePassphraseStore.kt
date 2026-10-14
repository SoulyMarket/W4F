package com.w4f.app.data.local

import android.content.Context
import android.util.Base64
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import java.security.SecureRandom
import javax.inject.Inject
import javax.inject.Singleton

/** Generates and stores the SQLCipher passphrase that encrypts the local
 * Room database at rest (section 6.12, section 8's "Room over SQLCipher").
 * The passphrase itself lives in the same Keystore-backed storage as the
 * session tokens (`EncryptedTokenStore`) — never in plain SharedPreferences,
 * never logged. Generated once on first run; losing it means the local
 * database is unrecoverable, which is acceptable here since it's a cache +
 * outbox, not the system of record (the backend is). */
@Singleton
class DatabasePassphraseStore @Inject constructor(@ApplicationContext context: Context) {

  private val prefs by lazy {
    val masterKey = MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
    EncryptedSharedPreferences.create(
      context,
      "w4f_db_prefs",
      masterKey,
      EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
      EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )
  }

  fun getOrCreatePassphrase(): ByteArray {
    val existing = prefs.getString(KEY_PASSPHRASE, null)
    if (existing != null) return Base64.decode(existing, Base64.NO_WRAP)

    val generated = ByteArray(32).also { SecureRandom().nextBytes(it) }
    prefs.edit().putString(KEY_PASSPHRASE, Base64.encodeToString(generated, Base64.NO_WRAP)).apply()
    return generated
  }

  private companion object {
    const val KEY_PASSPHRASE = "db_passphrase"
  }
}
