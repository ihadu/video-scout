package com.videoscout.app.ui.player

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.pager.VerticalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import com.videoscout.app.data.model.Video

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun VerticalPlayerScreen(
    initialVideoId: Int,
    onBackClick: () -> Unit,
    viewModel: PlayerViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    // Create ExoPlayer
    val exoPlayer = remember { ExoPlayer.Builder(context).build() }

    DisposableEffect(Unit) {
        onDispose {
            exoPlayer.release()
        }
    }

    LaunchedEffect(initialVideoId) {
        viewModel.initialize(initialVideoId)
    }

    when (val state = uiState) {
        is PlayerUiState.Loading -> {
            Box(modifier = Modifier.fillMaxSize())
        }
        is PlayerUiState.Error -> {
            // Show error
        }
        is PlayerUiState.Success -> {
            val videos = state.videos
            val pagerState = rememberPagerState(
                initialPage = videos.indexOfFirst { it.id == initialVideoId }.coerceAtLeast(0),
                pageCount = { videos.size }
            )

            // Handle page changes
            LaunchedEffect(pagerState.settledPage) {
                viewModel.onPageChanged(pagerState.settledPage)
                val video = videos[pagerState.settledPage]
                playVideo(exoPlayer, video, viewModel)
            }

            VerticalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize(),
                beyondBoundsPageCount = 1
            ) { page ->
                val video = videos[page]
                VideoPlayerPage(
                    video = video,
                    isActive = page == pagerState.settledPage,
                    exoPlayer = exoPlayer,
                    onBackClick = onBackClick,
                    onFavoriteClick = { viewModel.toggleFavorite(video.id) },
                    onRateClick = { rating -> viewModel.rateVideo(video.id, rating) },
                    isFavorite = state.favoriteStates[video.id] ?: false,
                    currentRating = video.rating
                )
            }
        }
    }
}

private fun playVideo(exoPlayer: ExoPlayer, video: Video, viewModel: PlayerViewModel) {
    val serverUrl = viewModel.getCurrentServerUrl()
    val mediaItem = MediaItem.Builder()
        .setUri("$serverUrl/api/play/${video.id}")
        .build()

    exoPlayer.setMediaItem(mediaItem)
    exoPlayer.prepare()
    exoPlayer.playWhenReady = true
}
