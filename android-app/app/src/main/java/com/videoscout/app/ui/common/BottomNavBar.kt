package com.videoscout.app.ui.common

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.VideoLibrary
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavController
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.compose.currentBackStackEntryAsState
import com.videoscout.app.ui.navigation.Screen

sealed class BottomNavItem(
    val route: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val label: String
) {
    data object Discover : BottomNavItem(Screen.Discover.route, Icons.Default.Home, "发现")
    data object Library : BottomNavItem(Screen.Library.route, Icons.Default.VideoLibrary, "视频库")
    data object Favorites : BottomNavItem(Screen.Favorites.route, Icons.Default.Favorite, "收藏")
    data object History : BottomNavItem(Screen.History.route, Icons.Default.History, "历史")
}

val bottomNavItems = listOf(
    BottomNavItem.Discover,
    BottomNavItem.Library,
    BottomNavItem.Favorites,
    BottomNavItem.History
)

@Composable
fun BottomNavBar(
    navController: NavController,
    modifier: Modifier = Modifier
) {
    NavigationBar(modifier = modifier) {
        val navBackStackEntry = navController.currentBackStackEntryAsState()
        val currentDestination = navBackStackEntry.value?.destination

        bottomNavItems.forEach { item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = item.label) },
                label = { Text(item.label) },
                selected = currentDestination?.hierarchy?.any { it.route == item.route } == true,
                onClick = {
                    navController.navigate(item.route) {
                        popUpTo(navController.graph.startDestinationId) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    }
}
