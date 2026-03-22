package com.videoscout.app.utils

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import java.io.File
import java.net.InetAddress
import java.net.NetworkInterface
import java.text.DecimalFormat

object NetworkUtils {

    fun isNetworkAvailable(context: Context): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    fun isWifiConnected(context: Context): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    fun getLocalIpAddress(): String? {
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val networkInterface = interfaces.nextElement()
                val addresses = networkInterface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (!address.isLoopbackAddress && address is java.net.Inet4Address) {
                        return address.hostAddress
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return null
    }

    suspend fun testConnection(url: String, timeoutMs: Int = 2000): Boolean {
        return try {
            val host = url.replace("http://", "").replace("https://", "").substringBefore(":")
            val port = url.substringAfterLast(":", "80").toInt()
            val socket = java.net.Socket()
            socket.connect(java.net.InetSocketAddress(host, port), timeoutMs)
            socket.close()
            true
        } catch (e: Exception) {
            false
        }
    }
}

object CacheUtils {

    fun getCacheSize(cacheDir: File): Long {
        return getFolderSize(cacheDir)
    }

    fun clearCache(cacheDir: File) {
        cacheDir.listFiles()?.forEach { file ->
            if (file.isDirectory) {
                file.deleteRecursively()
            } else {
                file.delete()
            }
        }
    }

    private fun getFolderSize(folder: File): Long {
        if (!folder.exists()) return 0
        var size = 0L
        folder.listFiles()?.forEach { file ->
            size += if (file.isDirectory) getFolderSize(file) else file.length()
        }
        return size
    }

    fun formatFileSize(bytes: Long): String {
        if (bytes <= 0) return "0 B"
        val units = arrayOf("B", "KB", "MB", "GB", "TB")
        val digitGroups = (Math.log10(bytes.toDouble()) / Math.log10(1024.0)).toInt()
        val formatted = DecimalFormat("#,##0.#").format(
            bytes / Math.pow(1024.0, digitGroups.toDouble())
        )
        return "$formatted ${units[digitGroups.coerceIn(0, units.size - 1)]}"
    }
}

object TimeUtils {

    fun formatDuration(seconds: Long): String {
        val hours = seconds / 3600
        val minutes = (seconds % 3600) / 60
        val secs = seconds % 60

        return if (hours > 0) {
            String.format("%02d:%02d:%02d", hours, minutes, secs)
        } else {
            String.format("%02d:%02d", minutes, secs)
        }
    }

    fun formatDurationFromMs(milliseconds: Long): String {
        return formatDuration(milliseconds / 1000)
    }

    fun formatDurationSeconds(seconds: Double?): String {
        if (seconds == null) return "00:00"
        return formatDuration(seconds.toLong())
    }
}
