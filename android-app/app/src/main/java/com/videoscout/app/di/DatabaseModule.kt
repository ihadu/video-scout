package com.videoscout.app.di

import android.content.Context
import androidx.room.Room
import com.videoscout.app.data.local.VideoScoutDatabase
import com.videoscout.app.data.local.dao.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): VideoScoutDatabase {
        return Room.databaseBuilder(
            context,
            VideoScoutDatabase::class.java,
            VideoScoutDatabase.DATABASE_NAME
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun provideVideoDao(database: VideoScoutDatabase): VideoDao {
        return database.videoDao()
    }

    @Provides
    fun provideCategoryDao(database: VideoScoutDatabase): CategoryDao {
        return database.categoryDao()
    }

    @Provides
    fun provideTagDao(database: VideoScoutDatabase): TagDao {
        return database.tagDao()
    }

    @Provides
    fun provideFavoriteDao(database: VideoScoutDatabase): FavoriteDao {
        return database.favoriteDao()
    }

    @Provides
    fun provideHistoryDao(database: VideoScoutDatabase): HistoryDao {
        return database.historyDao()
    }

    @Provides
    fun provideThumbnailCacheDao(database: VideoScoutDatabase): ThumbnailCacheDao {
        return database.thumbnailCacheDao()
    }
}
