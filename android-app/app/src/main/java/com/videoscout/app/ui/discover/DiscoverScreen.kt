package com.videoscout.app.ui.discover

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import com.videoscout.app.data.model.Video
import com.videoscout.app.utils.UrlBuilder

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiscoverScreen(
    onVideoClick: (Int) -> Unit,
    onNavigateToSettings: () -> Unit,
    viewModel: DiscoverViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("发现") },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "设置"
                        )
                    }
                }
            )
        }
    ) { padding ->
        when (val state = uiState) {
            is DiscoverUiState.Loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            is DiscoverUiState.Error -> {
                ErrorMessage(
                    message = state.message,
                    onRetry = { viewModel.refresh() }
                )
            }
            is DiscoverUiState.Success -> {
                VideoCardGrid(
                    videos = state.videos,
                    onVideoClick = onVideoClick,
                    viewModel = viewModel,
                    modifier = Modifier.padding(padding)
                )
            }
        }
    }
}

@Composable
fun VideoCardGrid(
    videos: List<Video>,
    onVideoClick: (Int) -> Unit,
    viewModel: DiscoverViewModel,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.fillMaxSize()) {
        if (videos.isNotEmpty()) {
            // Featured video - large card
            FeaturedVideoCard(
                video = videos.first(),
                onClick = { onVideoClick(videos.first().id) },
                viewModel = viewModel,
                modifier = Modifier.padding(16.dp)
            )

            // More videos grid
            Text(
                text = "推荐视频",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )

            // Grid of smaller cards
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                contentPadding = PaddingValues(16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                items(videos.drop(1)) { video ->
                    VideoCard(
                        video = video,
                        viewModel = viewModel,
                        onClick = { onVideoClick(video.id) }
                    )
                }
            }
        }
    }
}

@Composable
fun FeaturedVideoCard(
    video: Video,
    onClick: () -> Unit,
    viewModel: DiscoverViewModel,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier
            .fillMaxWidth()
            .height(200.dp)
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            // Thumbnail
            AsyncImage(
                model = viewModel.getThumbnailUrl(video.id),
                contentDescription = video.displayTitle,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            // Play button overlay
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.PlayArrow,
                    contentDescription = "播放",
                    modifier = Modifier.size(64.dp),
                    tint = Color.White.copy(alpha = 0.9f)
                )
            }

            // Info overlay
            Column(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .padding(16.dp)
            ) {
                Text(
                    text = video.displayTitle,
                    style = MaterialTheme.typography.titleMedium,
                    color = Color.White
                )
                Text(
                    text = "${video.displayDuration} · ${video.displaySize}",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color.White.copy(alpha = 0.8f)
                )
            }
        }
    }
}

@Composable
fun VideoCard(
    video: Video,
    viewModel: DiscoverViewModel,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(16f / 9f)
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            AsyncImage(
                model = viewModel.getThumbnailUrl(video.id),
                contentDescription = video.displayTitle,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            // Duration badge
            Surface(
                color = Color.Black.copy(alpha = 0.7f),
                shape = MaterialTheme.shapes.small,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(8.dp)
            ) {
                Text(
                    text = video.displayDuration,
                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp),
                    color = Color.White,
                    style = MaterialTheme.typography.labelSmall
                )
            }
        }
    }
}

@Composable
fun ErrorMessage(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = message,
            style = MaterialTheme.typography.bodyLarge
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onRetry) {
            Text("重试")
        }
    }
}
