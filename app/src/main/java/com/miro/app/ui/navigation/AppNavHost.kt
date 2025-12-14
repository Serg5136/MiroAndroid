package com.miro.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.miro.app.ui.BoardDetailViewModel
import com.miro.app.ui.BoardListViewModel
import com.miro.app.ui.screens.BoardDetailRoute
import com.miro.app.ui.screens.BoardListRoute

object Destinations {
    const val BOARD_LIST = "board_list"
    const val BOARD_DETAIL = "board_detail/{boardId}"
}

@Composable
fun AppNavHost(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController(),
    boardListViewModelFactory: () -> ViewModelProvider.Factory,
    boardDetailViewModelFactory: (String) -> ViewModelProvider.Factory,
    startBoardId: String? = null,
) {
    NavHost(
        navController = navController,
        startDestination = Destinations.BOARD_LIST,
        modifier = modifier,
    ) {
        composable(Destinations.BOARD_LIST) {
            val viewModel: BoardListViewModel = viewModel(factory = boardListViewModelFactory())
            val listState by viewModel.uiState.collectAsStateWithLifecycle()
            BoardListRoute(
                state = listState,
                onRefresh = viewModel::refresh,
                onBoardClick = { boardId ->
                    navController.navigate("board_detail/$boardId")
                },
            )
        }

        composable(
            route = Destinations.BOARD_DETAIL,
            arguments = listOf(navArgument("boardId") { type = NavType.StringType })
        ) { backStackEntry ->
            val boardId = backStackEntry.arguments?.getString("boardId") ?: return@composable
            val viewModel: BoardDetailViewModel = viewModel(
                factory = boardDetailViewModelFactory(boardId)
            )
            val detailState by viewModel.uiState.collectAsStateWithLifecycle()
            BoardDetailRoute(
                state = detailState,
                onRetry = viewModel::retry,
                onBack = navController::popBackStack,
            )
        }
    }

    LaunchedEffect(startBoardId) {
        val boardId = startBoardId ?: return@LaunchedEffect
        navController.navigate("board_detail/$boardId")
    }
}
