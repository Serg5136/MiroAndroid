package com.miro.app

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.miro.app.analytics.AnalyticsLogger
import com.miro.app.di.AppContainer
import com.miro.app.ui.BoardDetailViewModel
import com.miro.app.ui.BoardListViewModel
import com.miro.app.ui.navigation.AppNavHost
import com.miro.app.ui.permissions.NotificationPermissionRequester

class MainActivity : ComponentActivity() {

    private lateinit var container: AppContainer
    private var startBoardId: String? by mutableStateOf(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        container = AppContainer(applicationContext)
        startBoardId = parseBoardIdFromIntent(intent)
        startBoardId?.let { AnalyticsLogger.logNotificationTapped(it) }

        setContent {
            NotificationPermissionRequester()
            AppNavHost(
                boardListViewModelFactory = { boardListViewModelFactory() },
                boardDetailViewModelFactory = { id -> boardDetailViewModelFactory(id) },
                startBoardId = startBoardId,
            )
        }
    }

    override fun onNewIntent(intent: android.content.Intent?) {
        super.onNewIntent(intent)
        val boardId = parseBoardIdFromIntent(intent)
        if (boardId != null) {
            startBoardId = boardId
            AnalyticsLogger.logNotificationTapped(boardId)
        }
    }

    private fun boardListViewModelFactory(): ViewModelProvider.Factory =
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return BoardListViewModel(container.getBoardsUseCase) as T
            }
        }

    private fun boardDetailViewModelFactory(boardId: String): ViewModelProvider.Factory =
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return BoardDetailViewModel(boardId, container.getBoardDetailUseCase) as T
            }
        }

    private fun parseBoardIdFromIntent(intent: Intent?): String? {
        val data = intent?.data ?: return null
        val segments = data.pathSegments
        if (segments.isEmpty()) return null
        return segments.lastOrNull()
    }
}
