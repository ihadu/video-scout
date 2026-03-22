package com.videoscout.app.ui.library

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.model.Category
import com.videoscout.app.data.model.Tag
import com.videoscout.app.data.model.Video
import com.videoscout.app.data.repository.VideoRepository
import com.videoscout.app.utils.UrlBuilder
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LibraryUiState(
    val videos: List<Video> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
    val selectedCategory: Category? = null,
    val selectedTag: Tag? = null
)

@HiltViewModel
class LibraryViewModel @Inject constructor(
    private val videoRepository: VideoRepository,
    private val urlBuilder: UrlBuilder
) : ViewModel() {

    private val _uiState = MutableStateFlow(LibraryUiState())
    val uiState: StateFlow<LibraryUiState> = _uiState.asStateFlow()

    private val _categories = MutableStateFlow<List<Category>>(emptyList())
    val categories: StateFlow<List<Category>> = _categories.asStateFlow()

    private val _tags = MutableStateFlow<List<Tag>>(emptyList())
    val tags: StateFlow<List<Tag>> = _tags.asStateFlow()

    init {
        loadVideos()
        // 启动时自动同步服务器数据
        refreshVideos()
    }

    private fun refreshVideos() {
        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true, errorMessage = null) }
            try {
                videoRepository.refreshVideos()
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        errorMessage = "同步失败: ${e.message ?: "请检查服务器地址设置"}"
                    )
                }
            } finally {
                _uiState.update { it.copy(isRefreshing = false) }
            }
        }
    }

    private fun loadVideos() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            try {
                videoRepository.getVideos().collect { videos ->
                    _uiState.update {
                        it.copy(
                            videos = filterVideos(videos),
                            isLoading = false
                        )
                    }
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    fun refresh() {
        refreshVideos()
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }

    fun selectCategory(category: Category?) {
        _uiState.update { it.copy(selectedCategory = category) }
        refreshFilter()
    }

    fun selectTag(tag: Tag?) {
        _uiState.update { it.copy(selectedTag = tag) }
        refreshFilter()
    }

    private fun refreshFilter() {
        // Reload with filter
        loadVideos()
    }

    private fun filterVideos(videos: List<Video>): List<Video> {
        return videos.filter { video ->
            val categoryMatch = _uiState.value.selectedCategory?.let { cat ->
                video.categories.any { it.id == cat.id }
            } ?: true

            val tagMatch = _uiState.value.selectedTag?.let { tag ->
                video.tags.any { it.id == tag.id }
            } ?: true

            categoryMatch && tagMatch
        }
    }

    fun getThumbnailUrl(videoId: Int): String = urlBuilder.getThumbnailUrl(videoId)
}
