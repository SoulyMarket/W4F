package com.w4f.app.di

import com.w4f.app.data.local.EncryptedTokenStore
import com.w4f.app.data.local.TokenStore
import com.w4f.app.data.repository.AuthRepository
import com.w4f.app.data.repository.DefaultAuthRepository
import com.w4f.app.data.repository.DefaultDouarRepository
import com.w4f.app.data.repository.DefaultReportRepository
import com.w4f.app.data.repository.DouarRepository
import com.w4f.app.data.repository.ReportRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

  @Binds @Singleton abstract fun bindTokenStore(impl: EncryptedTokenStore): TokenStore

  @Binds @Singleton abstract fun bindAuthRepository(impl: DefaultAuthRepository): AuthRepository

  @Binds @Singleton abstract fun bindDouarRepository(impl: DefaultDouarRepository): DouarRepository

  @Binds
  @Singleton
  abstract fun bindReportRepository(impl: DefaultReportRepository): ReportRepository
}
