package com.videoscout.app.ui.discover

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.model.Video
import com.videoscout.app.data.repository.RecommendRepository
import com.videoscout.app.utils.UrlBuilder
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class DiscoverUiState {
    object Loading : DiscoverUiState()
    data class Error(val message: String) : DiscoverUiState()
    data class Success(val videos: List<Video>) : DiscoverUiState()
}

@HiltViewModel
class DiscoverViewModel @Inject constructor(
    private val recommendRepository: RecommendRepository,
    private val urlBuilder: UrlBuilder
) : ViewModel() {

    private val _uiState = MutableStateFlow<DiscoverUiState>(DiscoverUiState.Loading)
    val uiState: StateFlow<DiscoverUiState> = _uiState.asStateFlow()

    init {
        loadRecommendations()
    }

    private fun loadRecommendations() {
        viewModelScope.launch {
            _uiState.value = DiscoverUiState.Loading
            recommendRepository.getRecommendations()
                .catch { e ->
                    _uiState.value = DiscoverUiState.Error(e.message ?: "加载失败")
                }
                .collect { videos ->
                    _uiState.value = DiscoverUiState.Success(videos)
                }
        }
    }

    fun refresh() {
        viewModelScope.launch {
            recommendRepository.refreshRecommendations()
        }
    }

    fun getThumbnailUrl(videoId: Int): String = urlBuilder.getThumbnailUrl(videoId)
}
