package com.videoscout.app.ui.favorites

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.model.Video
import com.videoscout.app.data.repository.FavoriteRepository
import com.videoscout.app.utils.UrlBuilder
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class FavoritesViewModel @Inject constructor(
    private val favoriteRepository: FavoriteRepository,
    private val urlBuilder: UrlBuilder
) : ViewModel() {

    private val _favorites = MutableStateFlow<List<Video>>(emptyList())
    val favorites: StateFlow<List<Video>> = _favorites.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadFavorites()
    }

    private fun loadFavorites() {
        viewModelScope.launch {
            _isLoading.value = true
            favoriteRepository.getFavorites()
                .catch { /* Handle error */ }
                .collect { videos ->
                    _favorites.value = videos
                    _isLoading.value = false
                }
        }
    }

    fun removeFavorite(videoId: Int) {
        viewModelScope.launch {
            favoriteRepository.removeFromFavorites(videoId)
        }
    }

    fun getThumbnailUrl(videoId: Int): String = urlBuilder.getThumbnailUrl(videoId)
}
