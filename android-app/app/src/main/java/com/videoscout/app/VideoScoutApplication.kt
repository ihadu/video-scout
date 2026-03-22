package com.videoscout.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class VideoScoutApplication : Application() {

    override fun onCreate() {
        super.onCreate()
    }
}
