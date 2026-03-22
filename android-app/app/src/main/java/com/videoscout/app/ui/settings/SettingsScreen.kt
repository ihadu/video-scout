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
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Warning
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.videoscout.app.data.repository.ConnectionTestResult

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onNavigateBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val serverUrl by viewModel.serverUrl.collectAsState()
    val cacheSize by viewModel.cacheSize.collectAsState()
    val connectionTestResult by viewModel.connectionTestResult.collectAsState()
    val isTestingConnection by viewModel.isTestingConnection.collectAsState()
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
                supportingContent = {
                    Column {
                        Text(serverUrl)
                        // Connection Test Result
                        if (connectionTestResult != null) {
                            ConnectionResultDisplay(result = connectionTestResult!!)
                        }
                    }
                },
                trailingContent = {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(
                            onClick = { viewModel.testConnection(serverUrl) },
                            enabled = !isTestingConnection
                        ) {
                            if (isTestingConnection) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(16.dp),
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Text("测试连接")
                            }
                        }
                        Button(onClick = { showServerDialog = true }) {
                            Text("配置")
                        }
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
            onTestConnection = { url ->
                viewModel.testConnection(url)
            },
            connectionTestResult = connectionTestResult,
            isTestingConnection = isTestingConnection,
            onSave = { url ->
                viewModel.setServerUrl(url)
                viewModel.clearConnectionTestResult()
                showServerDialog = false
            },
            onDismiss = {
                viewModel.clearConnectionTestResult()
                showServerDialog = false
            }
        )
    }
}

@Composable
fun ServerConfigDialog(
    currentUrl: String,
    onTestConnection: (String) -> Unit,
    connectionTestResult: ConnectionTestResult?,
    isTestingConnection: Boolean,
    onSave: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var url by remember { mutableStateOf(currentUrl) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("配置服务器") },
        text = {
            Column {
                OutlinedTextField(
                    value = url,
                    onValueChange = { url = it },
                    label = { Text("服务器地址") },
                    placeholder = { Text("http://192.168.1.1:8000") },
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Test connection button
                OutlinedButton(
                    onClick = { onTestConnection(url) },
                    enabled = !isTestingConnection && url.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (isTestingConnection) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("测试中...")
                    } else {
                        Text("测试连接")
                    }
                }

                // Show test result
                if (connectionTestResult != null) {
                    ConnectionResultDisplay(result = connectionTestResult)
                }
            }
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

@Composable
fun ConnectionResultDisplay(result: ConnectionTestResult) {
    when (result) {
        is ConnectionTestResult.Success -> {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                modifier = Modifier.padding(top = 8.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "连接成功",
                            color = MaterialTheme.colorScheme.primary,
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Text(
                        text = "响应时间: ${result.responseTimeMs}ms",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                    Text(
                        text = result.message,
                        style = MaterialTheme.typography.bodySmall,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }
        is ConnectionTestResult.Failure -> {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer
                ),
                modifier = Modifier.padding(top = 8.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Warning,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.error,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "连接失败",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Text(
                        text = "状态码: ${result.statusCode}",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                    Text(
                        text = result.errorMessage,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
        is ConnectionTestResult.Error -> {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer
                ),
                modifier = Modifier.padding(top = 8.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Clear,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.error,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "连接错误: ${result.errorType}",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    Text(
                        text = result.errorMessage,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.padding(top = 4.dp),
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
    }
}
