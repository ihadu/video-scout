package com.videoscout.app.di

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.videoscout.app.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import javax.inject.Inject
import javax.inject.Singleton

// 使用委托属性确保单例，在 Application 上下文只创建一次
private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "server_config")

@Singleton
class BaseUrlProvider @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val serverUrlKey = stringPreferencesKey("server_url")

    val baseUrl: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[serverUrlKey] ?: BuildConfig.DEFAULT_SERVER_URL
    }

    fun getCurrentBaseUrl(): String {
        return runBlocking(Dispatchers.IO) {
            baseUrl.first()
        }
    }
}
