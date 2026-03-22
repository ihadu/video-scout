package com.videoscout.app.utils

import com.videoscout.app.di.BaseUrlProvider
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UrlBuilder @Inject constructor(
    private val baseUrlProvider: BaseUrlProvider
) {
    fun getThumbnailUrl(videoId: Int): String {
        return "${baseUrlProvider.getCurrentBaseUrl()}/api/play/thumbnail/$videoId"
    }

    fun getVideoPlayUrl(videoId: Int): String {
        return "${baseUrlProvider.getCurrentBaseUrl()}/api/play/$videoId"
    }

    fun getBaseUrl(): String = baseUrlProvider.getCurrentBaseUrl()
}
