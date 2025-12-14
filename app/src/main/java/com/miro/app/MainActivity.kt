package com.miro.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.miro.app.di.AppContainer
import com.miro.app.ui.BoardDetailViewModel
import com.miro.app.ui.BoardListViewModel
import com.miro.app.ui.navigation.AppNavHost

class MainActivity : ComponentActivity() {

    private lateinit var container: AppContainer

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        container = AppContainer(applicationContext)

        setContent {
            AppNavHost(
                boardListViewModelFactory = { boardListViewModelFactory() },
                boardDetailViewModelFactory = { id -> boardDetailViewModelFactory(id) },
            )
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
}
