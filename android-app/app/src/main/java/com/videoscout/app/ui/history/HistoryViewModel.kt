package com.videoscout.app.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.model.Video
import com.videoscout.app.data.repository.HistoryRepository
import com.videoscout.app.utils.UrlBuilder
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val historyRepository: HistoryRepository,
    private val urlBuilder: UrlBuilder
) : ViewModel() {

    private val _history = MutableStateFlow<List<Video>>(emptyList())
    val history: StateFlow<List<Video>> = _history.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        loadHistory()
    }

    private fun loadHistory() {
        viewModelScope.launch {
            _isLoading.value = true
            historyRepository.getHistory()
                .catch { /* Handle error */ }
                .collect { videos ->
                    _history.value = videos
                    _isLoading.value = false
                }
        }
    }

    fun clearHistory() {
        viewModelScope.launch {
            historyRepository.clearHistory()
        }
    }

    fun getThumbnailUrl(videoId: Int): String = urlBuilder.getThumbnailUrl(videoId)
}
