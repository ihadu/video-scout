package com.videoscout.app.di

import android.content.Context
import com.videoscout.app.BuildConfig
import com.videoscout.app.data.remote.VideoScoutApi
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.Cache
import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        @ApplicationContext context: Context,
        dynamicBaseUrlInterceptor: DynamicBaseUrlInterceptor
    ): OkHttpClient {
        val cacheSize = 100 * 1024 * 1024L // 100MB cache
        val cache = Cache(File(context.cacheDir, "http_cache"), cacheSize)

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        return OkHttpClient.Builder()
            .cache(cache)
            .addInterceptor(dynamicBaseUrlInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        baseUrlProvider: BaseUrlProvider
    ): Retrofit {
        // Use a placeholder base URL - the actual URL will be set by interceptor
        val currentUrl = try {
            baseUrlProvider.getCurrentBaseUrl()
        } catch (e: Exception) {
            BuildConfig.DEFAULT_SERVER_URL
        }

        return Retrofit.Builder()
            .baseUrl(currentUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideVideoScoutApi(retrofit: Retrofit): VideoScoutApi {
        return retrofit.create(VideoScoutApi::class.java)
    }
}
