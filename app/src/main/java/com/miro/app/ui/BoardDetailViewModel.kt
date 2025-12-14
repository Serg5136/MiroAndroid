package com.miro.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.miro.app.domain.model.BoardSummary
import com.miro.app.domain.usecase.GetBoardDetailUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class BoardDetailUiState(
    val board: BoardSummary? = null,
    val isLoading: Boolean = true,
    val errorMessage: String? = null,
)

class BoardDetailViewModel(
    private val boardId: String,
    private val useCase: GetBoardDetailUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(BoardDetailUiState(isLoading = true))
    val uiState: StateFlow<BoardDetailUiState> = _uiState

    init {
        fetchBoard()
    }

    fun retry() = fetchBoard()

    private fun fetchBoard() {
        _uiState.update { it.copy(isLoading = true, errorMessage = null) }
        viewModelScope.launch {
            val result = useCase(boardId)
            _uiState.update { state ->
                result.fold(
                    onSuccess = { board -> state.copy(board = board, isLoading = false) },
                    onFailure = { error -> state.copy(isLoading = false, errorMessage = error.message) },
                )
            }
        }
    }
}
