package com.videoscout.app.di

import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DynamicBaseUrlInterceptor @Inject constructor(
    private val baseUrlProvider: BaseUrlProvider
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val originalUrl = originalRequest.url

        // Get current base URL from provider
        val currentBaseUrl = baseUrlProvider.getCurrentBaseUrl()
        val newBaseUrl = currentBaseUrl.toHttpUrlOrNull() ?: return chain.proceed(originalRequest)

        // Rebuild the URL with the new base
        val newUrl = originalUrl.newBuilder()
            .scheme(newBaseUrl.scheme)
            .host(newBaseUrl.host)
            .port(newBaseUrl.port)
            .build()

        // If URL changed, rebuild the request
        if (newUrl != originalUrl) {
            val newRequest = originalRequest.newBuilder()
                .url(newUrl)
                .build()
            return chain.proceed(newRequest)
        }

        return chain.proceed(originalRequest)
    }
}
