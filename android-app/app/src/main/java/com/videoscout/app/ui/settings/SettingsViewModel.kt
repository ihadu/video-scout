package com.videoscout.app.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.videoscout.app.data.repository.ConnectionTestResult
import com.videoscout.app.data.repository.ServerConfigRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val serverConfigRepository: ServerConfigRepository,
    private val cacheDir: File
) : ViewModel() {

    private val _serverUrl = MutableStateFlow("http://192.168.1.1:8000")
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val _cacheSize = MutableStateFlow(0L)
    val cacheSize: StateFlow<Long> = _cacheSize.asStateFlow()

    private val _connectionTestResult = MutableStateFlow<ConnectionTestResult?>(null)
    val connectionTestResult: StateFlow<ConnectionTestResult?> = _connectionTestResult.asStateFlow()

    private val _isTestingConnection = MutableStateFlow(false)
    val isTestingConnection: StateFlow<Boolean> = _isTestingConnection.asStateFlow()

    init {
        viewModelScope.launch {
            serverConfigRepository.getServerUrl().collect {
                _serverUrl.value = it
            }
        }
        calculateCacheSize()
    }

    fun setServerUrl(url: String) {
        viewModelScope.launch {
            serverConfigRepository.setServerUrl(url)
        }
    }

    fun discoverServer() {
        viewModelScope.launch {
            val discoveredUrl = serverConfigRepository.discoverServer()
            discoveredUrl?.let {
                _serverUrl.value = it
            }
        }
    }

    fun clearCache() {
        viewModelScope.launch {
            // Clear video cache
            val videoCacheDir = File(cacheDir, "video_cache")
            videoCacheDir.deleteRecursively()
            calculateCacheSize()
        }
    }

    private fun calculateCacheSize() {
        viewModelScope.launch {
            val videoCacheDir = File(cacheDir, "video_cache")
            _cacheSize.value = getFolderSize(videoCacheDir)
        }
    }

    fun testConnection(url: String) {
        viewModelScope.launch {
            _isTestingConnection.value = true
            _connectionTestResult.value = null
            val result = serverConfigRepository.testConnection(url)
            _connectionTestResult.value = result
            _isTestingConnection.value = false
        }
    }

    fun clearConnectionTestResult() {
        _connectionTestResult.value = null
    }

    private fun getFolderSize(folder: File): Long {
        if (!folder.exists()) return 0
        var size = 0L
        folder.listFiles()?.forEach { file ->
            size += if (file.isDirectory) getFolderSize(file) else file.length()
        }
        return size
    }
}
