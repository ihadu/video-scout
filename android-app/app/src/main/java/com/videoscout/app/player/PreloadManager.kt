package com.videoscout.app.player

import android.content.Context
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PreloadManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val maxPreloadCount = 2
    private val preloadPlayers = mutableListOf<PreloadPlayer>()

    data class PreloadPlayer(
        val videoId: Int,
        val player: ExoPlayer
    )

    @OptIn(UnstableApi::class)
    fun preload(videoId: Int, videoUrl: String) {
        // Check if already preloading
        if (preloadPlayers.any { it.videoId == videoId }) {
            return
        }

        // Clean up old preloads
        while (preloadPlayers.size >= maxPreloadCount) {
            preloadPlayers.removeFirstOrNull()?.let {
                it.player.release()
            }
        }

        scope.launch {
            val player = ExoPlayer.Builder(context).build().apply {
                setMediaItem(MediaItem.fromUri(videoUrl))
                volume = 0f
                prepare()
                playWhenReady = false
            }

            // Wait for buffering
            var attempts = 0
            while (attempts < 10 && player.bufferedPercentage < 20) {
                delay(100)
                attempts++
            }

            // If successfully buffered, add to pool
            if (player.bufferedPercentage >= 20) {
                preloadPlayers.add(PreloadPlayer(videoId, player))
            } else {
                player.release()
            }
        }
    }

    fun getPreloadedPlayer(videoId: Int): ExoPlayer? {
        return preloadPlayers.find { it.videoId == videoId }?.player
    }

    fun clearPreload(exceptVideoId: Int? = null) {
        preloadPlayers.filter { it.videoId != exceptVideoId }.forEach {
            it.player.release()
        }
        preloadPlayers.removeAll { it.videoId != exceptVideoId }
    }

    fun release() {
        preloadPlayers.forEach { it.player.release() }
        preloadPlayers.clear()
        scope.cancel()
    }
}
