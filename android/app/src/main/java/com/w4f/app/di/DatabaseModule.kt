package com.w4f.app.di

import android.content.Context
import androidx.room.Room
import com.w4f.app.data.local.DatabasePassphraseStore
import com.w4f.app.data.local.db.AppDatabase
import com.w4f.app.data.local.db.DouarDao
import com.w4f.app.data.local.db.ReportDao
import com.w4f.app.data.local.db.ReportMediaDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

  @Provides
  @Singleton
  fun provideAppDatabase(
    @ApplicationContext context: Context,
    passphraseStore: DatabasePassphraseStore,
  ): AppDatabase {
    // net.zetetic:sqlcipher-android doesn't load its native lib on class
    // init — nativeOpen() et al. fail with "No implementation found" until
    // this runs at least once (found on-device; nothing in a JVM/Robolectric
    // test exercises actual JNI linkage, so this was invisible until now).
    System.loadLibrary("sqlcipher")

    val passphrase = passphraseStore.getOrCreatePassphrase()
    return Room.databaseBuilder(context, AppDatabase::class.java, "w4f.db")
      .openHelperFactory(SupportOpenHelperFactory(passphrase))
      .fallbackToDestructiveMigration(true)
      .build()
  }

  @Provides fun provideDouarDao(db: AppDatabase): DouarDao = db.douarDao()

  @Provides fun provideReportDao(db: AppDatabase): ReportDao = db.reportDao()

  @Provides fun provideReportMediaDao(db: AppDatabase): ReportMediaDao = db.reportMediaDao()
}
