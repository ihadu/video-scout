package com.videoscout.app.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onNavigateBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val serverUrl by viewModel.serverUrl.collectAsState()
    val cacheSize by viewModel.cacheSize.collectAsState()
    var showServerDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("设置") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            // Server Settings
            ListItem(
                headlineContent = { Text("服务器地址") },
                supportingContent = { Text(serverUrl) },
                trailingContent = {
                    Button(onClick = { showServerDialog = true }) {
                        Text("配置")
                    }
                }
            )

            HorizontalDivider()

            // Cache Settings
            ListItem(
                headlineContent = { Text("缓存大小") },
                supportingContent = { Text(formatCacheSize(cacheSize)) },
                trailingContent = {
                    TextButton(onClick = { viewModel.clearCache() }) {
                        Text("清除缓存")
                    }
                }
            )

            HorizontalDivider()

            // Auto Scan Server
            ListItem(
                headlineContent = { Text("自动发现服务器") },
                supportingContent = { Text("扫描局域网内的 Video Scout 服务器") },
                trailingContent = {
                    Button(onClick = { viewModel.discoverServer() }) {
                        Text("扫描")
                    }
                }
            )
        }
    }

    if (showServerDialog) {
        ServerConfigDialog(
            currentUrl = serverUrl,
            onSave = { url ->
                viewModel.setServerUrl(url)
                showServerDialog = false
            },
            onDismiss = { showServerDialog = false }
        )
    }
}

@Composable
fun ServerConfigDialog(
    currentUrl: String,
    onSave: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var url by remember { mutableStateOf(currentUrl) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("配置服务器") },
        text = {
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("服务器地址") },
                placeholder = { Text("http://192.168.1.1:8000") }
            )
        },
        confirmButton = {
            TextButton(onClick = { onSave(url) }) {
                Text("保存")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

private fun formatCacheSize(bytes: Long): String {
    return when {
        bytes >= 1024 * 1024 * 1024 -> String.format("%.2f GB", bytes / (1024.0 * 1024.0 * 1024.0))
        bytes >= 1024 * 1024 -> String.format("%.2f MB", bytes / (1024.0 * 1024.0))
        bytes >= 1024 -> String.format("%.2f KB", bytes / 1024.0)
        else -> "$bytes B"
    }
}
