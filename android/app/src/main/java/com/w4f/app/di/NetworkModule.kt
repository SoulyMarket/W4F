package com.w4f.app.di

import com.w4f.app.BuildConfig
import com.w4f.app.data.local.TokenStore
import com.w4f.app.data.remote.AuthApi
import com.w4f.app.data.remote.MediaApi
import com.w4f.app.data.remote.ReportApi
import com.w4f.app.data.remote.SyncApi
import com.w4f.app.data.remote.TokenAuthenticator
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

  @Provides
  @Singleton
  fun provideJson(): Json = Json {
    ignoreUnknownKeys = true
    isLenient = true
  }

  /** Attaches the access token to every request; 401-handling (refresh +
   * retry, step 2.4) is `TokenAuthenticator`'s job, attached separately
   * below — an `Authenticator` runs only after a 401 comes back, whereas
   * this `Interceptor` runs on every outgoing request. */
  @Provides
  @Singleton
  fun provideAuthInterceptor(tokenStore: TokenStore): Interceptor = Interceptor { chain ->
    val token = tokenStore.getAccessToken()
    val request =
      if (token != null) {
        chain.request().newBuilder().addHeader("Authorization", "Bearer $token").build()
      } else {
        chain.request()
      }
    chain.proceed(request)
  }

  @Provides
  @Singleton
  fun provideOkHttpClient(authInterceptor: Interceptor, authenticator: TokenAuthenticator): OkHttpClient {
    val logging =
      HttpLoggingInterceptor().apply {
        // BODY logging would put request/response payloads (which can
        // include auth tokens in headers, though not bodies here) in
        // logcat — section 6.12: no tokens in logs. Headers excluded by
        // using BASIC rather than HEADERS/BODY level.
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE
      }
    return OkHttpClient.Builder()
      .addInterceptor(authInterceptor)
      .authenticator(authenticator)
      .addInterceptor(logging)
      .build()
  }

  @Provides
  @Singleton
  fun provideRetrofit(okHttpClient: OkHttpClient, json: Json): Retrofit =
    Retrofit.Builder()
      .baseUrl(BuildConfig.API_BASE_URL)
      .client(okHttpClient)
      .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
      .build()

  @Provides @Singleton fun provideAuthApi(retrofit: Retrofit): AuthApi = retrofit.create(AuthApi::class.java)

  @Provides @Singleton fun provideSyncApi(retrofit: Retrofit): SyncApi = retrofit.create(SyncApi::class.java)

  @Provides @Singleton fun provideMediaApi(retrofit: Retrofit): MediaApi = retrofit.create(MediaApi::class.java)

  @Provides @Singleton fun provideReportApi(retrofit: Retrofit): ReportApi = retrofit.create(ReportApi::class.java)
}
