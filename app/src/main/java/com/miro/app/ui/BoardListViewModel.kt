package com.miro.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.SavedStateHandle
import com.miro.app.domain.model.BoardSummary
import com.miro.app.domain.usecase.GetBoardsUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.Serializable

data class BoardListUiState(
    val boards: List<BoardSummary> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val loadingProgress: Float? = null,
) : Serializable

class BoardListViewModel(
    private val getBoardsUseCase: GetBoardsUseCase,
    private val savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        savedStateHandle[STATE_KEY] ?: BoardListUiState(isLoading = true)
    )
    val uiState: StateFlow<BoardListUiState> = _uiState

    init {
        if (_uiState.value.boards.isNotEmpty()) {
            updateState { it.copy(isLoading = false, loadingProgress = null) }
        } else {
            loadBoards()
        }
    }

    fun refresh() {
        loadBoards(forceRefresh = true)
    }

    private fun loadBoards(forceRefresh: Boolean = false) {
        updateState { it.copy(isLoading = true, errorMessage = null, loadingProgress = 0f) }
        viewModelScope.launch {
            updateProgress(0.3f)
            val result = getBoardsUseCase(forceRefresh)
            updateProgress(0.6f)
            updateState { state ->
                result.fold(
                    onSuccess = { boards ->
                        state.copy(
                            boards = boards,
                            isLoading = false,
                            errorMessage = null,
                            loadingProgress = null,
                        )
                    },
                    onFailure = { error ->
                        state.copy(
                            isLoading = false,
                            errorMessage = error.message ?: "",
                            loadingProgress = null,
                        )
                    }
                )
            }
        }
    }

    private fun updateState(reducer: (BoardListUiState) -> BoardListUiState) {
        _uiState.update { current ->
            reducer(current).also { savedStateHandle[STATE_KEY] = it }
        }
    }

    private fun updateProgress(progress: Float) {
        updateState { it.copy(loadingProgress = progress.coerceIn(0f, 1f)) }
    }

    private companion object {
        const val STATE_KEY = "board_list_state"
    }
}
