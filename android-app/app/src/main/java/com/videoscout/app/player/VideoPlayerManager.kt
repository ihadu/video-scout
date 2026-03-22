package com.videoscout.app.player

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject

sealed class PlayerState {
    object Idle : PlayerState()
    object Loading : PlayerState()
    object Ready : PlayerState()
    data class Playing(val isPlaying: Boolean) : PlayerState()
    data class Error(val message: String) : PlayerState()
    object Ended : PlayerState()
}

class VideoPlayerManager @Inject constructor(
    val exoPlayer: ExoPlayer
) {

    private val _playerState = MutableStateFlow<PlayerState>(PlayerState.Idle)
    val playerState: StateFlow<PlayerState> = _playerState.asStateFlow()

    private val _currentPosition = MutableStateFlow(0L)
    val currentPosition: StateFlow<Long> = _currentPosition.asStateFlow()

    private val _duration = MutableStateFlow(0L)
    val duration: StateFlow<Long> = _duration.asStateFlow()

    init {
        exoPlayer.addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {
                when (playbackState) {
                    Player.STATE_IDLE -> _playerState.value = PlayerState.Idle
                    Player.STATE_BUFFERING -> _playerState.value = PlayerState.Loading
                    Player.STATE_READY -> _playerState.value = PlayerState.Ready
                    Player.STATE_ENDED -> _playerState.value = PlayerState.Ended
                }
            }

            override fun onIsPlayingChanged(isPlaying: Boolean) {
                _playerState.value = PlayerState.Playing(isPlaying)
            }

            override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                _playerState.value = PlayerState.Error(error.message ?: "播放错误")
            }
        })
    }

    fun playVideo(videoId: Int, videoUrl: String, startPosition: Long = 0) {
        val mediaItem = MediaItem.Builder()
            .setUri(videoUrl)
            .build()

        exoPlayer.setMediaItem(mediaItem)
        exoPlayer.prepare()
        exoPlayer.seekTo(startPosition)
        exoPlayer.playWhenReady = true
    }

    fun pause() {
        exoPlayer.playWhenReady = false
    }

    fun play() {
        exoPlayer.playWhenReady = true
    }

    fun release() {
        exoPlayer.release()
    }
}

@Composable
fun rememberExoPlayerWithLifecycle(): ExoPlayer {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle

    val player = remember {
        ExoPlayer.Builder(context).build()
    }

    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_PAUSE -> player.pause()
                Lifecycle.Event.ON_RESUME -> player.play()
                Lifecycle.Event.ON_DESTROY -> player.release()
                else -> {}
            }
        }
        lifecycle.addObserver(observer)
        onDispose {
            lifecycle.removeObserver(observer)
            player.release()
        }
    }

    return player
}
