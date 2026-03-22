package com.videoscout.app.ui.player

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.FavoriteBorder
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import coil.compose.AsyncImage
import com.videoscout.app.data.model.Video
import kotlinx.coroutines.delay

@Composable
fun VideoPlayerPage(
    video: Video,
    isActive: Boolean,
    exoPlayer: ExoPlayer,
    onBackClick: () -> Unit,
    onFavoriteClick: () -> Unit,
    onRateClick: (Int) -> Unit,
    isFavorite: Boolean,
    currentRating: Int,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var showControls by remember { mutableStateOf(false) }
    var showRatingDialog by remember { mutableStateOf(false) }

    // Auto-hide controls
    LaunchedEffect(showControls) {
        if (showControls) {
            delay(3000)
            showControls = false
        }
    }

    // Play/pause based on active state
    LaunchedEffect(isActive) {
        if (isActive) {
            exoPlayer.playWhenReady = true
        } else {
            exoPlayer.playWhenReady = false
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black)
            .pointerInput(Unit) {
                detectTapGestures {
                    showControls = !showControls
                }
            }
    ) {
        // Video Player
        AndroidView(
            factory = {
                PlayerView(context).apply {
                    layoutParams = FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                    useController = false
                    player = exoPlayer
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // Overlay Controls
        AnimatedVisibility(
            visible = showControls,
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            PlayerOverlayControls(
                video = video,
                isFavorite = isFavorite,
                currentRating = currentRating,
                onBackClick = onBackClick,
                onFavoriteClick = onFavoriteClick,
                onRateClick = { showRatingDialog = true }
            )
        }

        // Rating Dialog
        if (showRatingDialog) {
            RatingDialog(
                currentRating = currentRating,
                onRatingSelected = {
                    onRateClick(it)
                    showRatingDialog = false
                },
                onDismiss = { showRatingDialog = false }
            )
        }

        // Bottom Video Info
        VideoInfoOverlay(
            video = video,
            modifier = Modifier.align(Alignment.BottomStart)
        )
    }
}

@Composable
fun PlayerOverlayControls(
    video: Video,
    isFavorite: Boolean,
    currentRating: Int,
    onBackClick: () -> Unit,
    onFavoriteClick: () -> Unit,
    onRateClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.3f))
    ) {
        // Top bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBackClick) {
                Icon(
                    imageVector = Icons.Default.ArrowBack,
                    contentDescription = "返回",
                    tint = Color.White
                )
            }
        }

        // Right side controls
        Column(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Favorite button
            IconButton(onClick = onFavoriteClick) {
                Icon(
                    imageVector = if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                    contentDescription = if (isFavorite) "取消收藏" else "收藏",
                    tint = if (isFavorite) Color.Red else Color.White
                )
            }

            // Rating button
            IconButton(onClick = onRateClick) {
                Icon(
                    imageVector = Icons.Default.Star,
                    contentDescription = "评分",
                    tint = if (currentRating > 0) Color.Yellow else Color.White
                )
            }
        }
    }
}

@Composable
fun VideoInfoOverlay(
    video: Video,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(
                Brush.verticalGradient(
                    colors = listOf(Color.Transparent, Color.Black.copy(alpha = 0.7f))
                )
            )
            .padding(16.dp)
    ) {
        Text(
            text = video.displayTitle,
            color = Color.White,
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleMedium
        )

        Spacer(modifier = Modifier.height(4.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = video.displayDuration,
                color = Color.White.copy(alpha = 0.8f),
                style = MaterialTheme.typography.bodySmall
            )

            Text(
                text = video.displaySize,
                color = Color.White.copy(alpha = 0.8f),
                style = MaterialTheme.typography.bodySmall
            )

            if (video.rating > 0) {
                Text(
                    text = "★ ${video.rating}",
                    color = Color.Yellow,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }

        // Categories and Tags
        if (video.categories.isNotEmpty() || video.tags.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                video.categories.forEach { category ->
                    CategoryTagChip(name = category.name)
                }
                video.tags.forEach { tag ->
                    CategoryTagChip(name = tag.name)
                }
            }
        }
    }
}

@Composable
fun CategoryTagChip(name: String) {
    Surface(
        color = MaterialTheme.colorScheme.primary.copy(alpha = 0.8f),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            text = name,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            color = Color.White,
            style = MaterialTheme.typography.labelSmall
        )
    }
}

@Composable
fun RatingDialog(
    currentRating: Int,
    onRatingSelected: (Int) -> Unit,
    onDismiss: () -> Unit
) {
    var selectedRating by remember { mutableStateOf(currentRating) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("评分") },
        text = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                (1..5).forEach { rating ->
                    IconButton(onClick = { selectedRating = rating }) {
                        Icon(
                            imageVector = Icons.Default.Star,
                            contentDescription = "$rating 星",
                            tint = if (rating <= selectedRating) Color.Yellow else Color.Gray
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { onRatingSelected(selectedRating) }) {
                Text("确定")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}
