package com.videoscout.app.ui.player

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.model.Video
import com.videoscout.app.di.BaseUrlProvider
import com.videoscout.app.data.repository.FavoriteRepository
import com.videoscout.app.data.repository.RecommendRepository
import com.videoscout.app.data.repository.VideoRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class PlayerUiState {
    object Loading : PlayerUiState()
    data class Error(val message: String) : PlayerUiState()
    data class Success(
        val videos: List<Video> = emptyList(),
        val currentIndex: Int = 0,
        val favoriteStates: Map<Int, Boolean> = emptyMap()
    ) : PlayerUiState()
}

@HiltViewModel
class PlayerViewModel @Inject constructor(
    private val recommendRepository: RecommendRepository,
    private val favoriteRepository: FavoriteRepository,
    private val videoRepository: VideoRepository,
    private val baseUrlProvider: BaseUrlProvider
) : ViewModel() {

    private val _uiState = MutableStateFlow<PlayerUiState>(PlayerUiState.Loading)
    val uiState: StateFlow<PlayerUiState> = _uiState.asStateFlow()

    private val _playlist = MutableStateFlow<List<Video>>(emptyList())

    private var currentVideoIndex = 0

    fun initialize(initialVideoId: Int) {
        viewModelScope.launch {
            _uiState.value = PlayerUiState.Loading
            try {
                recommendRepository.getRecommendations().collectLatest { videos ->
                    _playlist.value = videos

                    // Load favorite states
                    val favoriteStates = mutableMapOf<Int, Boolean>()
                    videos.forEach { video ->
                        favoriteRepository.isFavorite(video.id).collect { isFav ->
                            favoriteStates[video.id] = isFav
                        }
                    }

                    _uiState.value = PlayerUiState.Success(
                        videos = videos,
                        currentIndex = videos.indexOfFirst { it.id == initialVideoId }.coerceAtLeast(0),
                        favoriteStates = favoriteStates.toMap()
                    )
                }
            } catch (e: Exception) {
                _uiState.value = PlayerUiState.Error(e.message ?: "加载失败")
            }
        }
    }

    fun onPageChanged(index: Int) {
        currentVideoIndex = index
        _uiState.update { currentState ->
            if (currentState is PlayerUiState.Success) {
                currentState.copy(currentIndex = index)
            } else currentState
        }
    }

    fun toggleFavorite(videoId: Int) {
        viewModelScope.launch {
            val currentState = (_uiState.value as? PlayerUiState.Success) ?: return@launch
            val isCurrentlyFavorite = currentState.favoriteStates[videoId] ?: false

            _uiState.update { state ->
                if (state is PlayerUiState.Success) {
                    state.copy(
                        favoriteStates = state.favoriteStates.toMutableMap().apply {
                            put(videoId, !isCurrentlyFavorite)
                        }
                    )
                } else state
            }

            if (isCurrentlyFavorite) {
                favoriteRepository.removeFromFavorites(videoId)
            } else {
                favoriteRepository.addToFavorites(videoId)
            }
        }
    }

    fun rateVideo(videoId: Int, rating: Int) {
        viewModelScope.launch {
            videoRepository.updateVideoRating(videoId, rating)
        }
    }

    fun getCurrentServerUrl(): String = baseUrlProvider.getCurrentBaseUrl()
}
