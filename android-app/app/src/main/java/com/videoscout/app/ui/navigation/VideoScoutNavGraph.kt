package com.videoscout.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.videoscout.app.ui.discover.DiscoverScreen
import com.videoscout.app.ui.favorites.FavoritesScreen
import com.videoscout.app.ui.history.HistoryScreen
import com.videoscout.app.ui.library.LibraryScreen
import com.videoscout.app.ui.player.VerticalPlayerScreen
import com.videoscout.app.ui.settings.SettingsScreen

sealed class Screen(val route: String) {
    data object Discover : Screen("discover")
    data object Library : Screen("library")
    data object Favorites : Screen("favorites")
    data object History : Screen("history")
    data object Settings : Screen("settings")
    data object Player : Screen("player/{videoId}") {
        fun createRoute(videoId: Int) = "player/$videoId"
    }
}

@Composable
fun VideoScoutNavGraph(
    navController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Discover.route,
        modifier = modifier
    ) {
        composable(Screen.Discover.route) {
            DiscoverScreen(
                onVideoClick = { videoId ->
                    navController.navigate(Screen.Player.createRoute(videoId))
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }

        composable(Screen.Library.route) {
            LibraryScreen(
                onVideoClick = { videoId ->
                    navController.navigate(Screen.Player.createRoute(videoId))
                }
            )
        }

        composable(Screen.Favorites.route) {
            FavoritesScreen(
                onVideoClick = { videoId ->
                    navController.navigate(Screen.Player.createRoute(videoId))
                }
            )
        }

        composable(Screen.History.route) {
            HistoryScreen(
                onVideoClick = { videoId ->
                    navController.navigate(Screen.Player.createRoute(videoId))
                }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            route = Screen.Player.route,
            arguments = listOf(
                navArgument("videoId") { type = NavType.IntType }
            )
        ) { backStackEntry ->
            val videoId = backStackEntry.arguments?.getInt("videoId") ?: 0
            VerticalPlayerScreen(
                initialVideoId = videoId,
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }
    }
}
