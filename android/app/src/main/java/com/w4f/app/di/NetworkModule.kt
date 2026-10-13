package com.w4f.app.di

import com.w4f.app.BuildConfig
import com.w4f.app.data.local.TokenStore
import com.w4f.app.data.remote.AuthApi
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

  /** Attaches the access token to every request. Does NOT handle refresh-on-
   * 401 yet — see step 2.4 (sync workers), where a 401 mid-background-sync
   * needs a real retry-after-refresh policy; a login screen can just send
   * the user back to re-authenticate for now. */
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
  fun provideOkHttpClient(authInterceptor: Interceptor): OkHttpClient {
    val logging =
      HttpLoggingInterceptor().apply {
        // BODY logging would put request/response payloads (which can
        // include auth tokens in headers, though not bodies here) in
        // logcat — section 6.12: no tokens in logs. Headers excluded by
        // using BASIC rather than HEADERS/BODY level.
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE
      }
    return OkHttpClient.Builder().addInterceptor(authInterceptor).addInterceptor(logging).build()
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
}
