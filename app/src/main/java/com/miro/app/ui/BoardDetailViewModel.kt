package com.miro.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.SavedStateHandle
import com.miro.app.domain.model.BoardSummary
import com.miro.app.domain.usecase.GetBoardDetailUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.Serializable

data class BoardDetailUiState(
    val board: BoardSummary? = null,
    val isLoading: Boolean = true,
    val errorMessage: String? = null,
    val loadingProgress: Float? = null,
) : Serializable

class BoardDetailViewModel(
    private val boardId: String,
    private val useCase: GetBoardDetailUseCase,
    private val savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        savedStateHandle[STATE_KEY] ?: BoardDetailUiState(isLoading = true)
    )
    val uiState: StateFlow<BoardDetailUiState> = _uiState

    init {
        if (_uiState.value.board != null) {
            updateState { it.copy(isLoading = false, loadingProgress = null) }
        } else {
            fetchBoard()
        }
    }

    fun retry() = fetchBoard()

    private fun fetchBoard() {
        updateState { it.copy(isLoading = true, errorMessage = null, board = null, loadingProgress = 0f) }
        viewModelScope.launch {
            updateProgress(0.4f)
            val result = useCase(boardId)
            updateProgress(0.7f)
            updateState { state ->
                result.fold(
                    onSuccess = { board ->
                        state.copy(
                            board = board,
                            isLoading = false,
                            errorMessage = null,
                            loadingProgress = null,
                        )
                    },
                    onFailure = { error ->
                        state.copy(
                            isLoading = false,
                            errorMessage = error.message,
                            board = null,
                            loadingProgress = null,
                        )
                    },
                )
            }
        }
    }

    private fun updateState(reducer: (BoardDetailUiState) -> BoardDetailUiState) {
        _uiState.update { current ->
            reducer(current).also { savedStateHandle[STATE_KEY] = it }
        }
    }

    private fun updateProgress(progress: Float?) {
        progress ?: return
        updateState { it.copy(loadingProgress = progress.coerceIn(0f, 1f)) }
    }

    private companion object {
        const val STATE_KEY = "board_detail_state"
    }
}
