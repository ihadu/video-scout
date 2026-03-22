// Top-level build file
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.kapt) apply false
    alias(libs.plugins.dagger.hilt) apply false
    alias(libs.plugins.compose.compiler) apply false
}

buildscript {
    extra.apply {
        set("compose_version", "1.6.1")
        set("exoplayer_version", "2.19.1")
        set("room_version", "2.6.1")
        set("hilt_version", "2.50")
    }
}
