package com.miro.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.miro.app.domain.model.BoardSummary
import com.miro.app.domain.usecase.GetBoardsUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class BoardListUiState(
    val boards: List<BoardSummary> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

class BoardListViewModel(
    private val getBoardsUseCase: GetBoardsUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(BoardListUiState(isLoading = true))
    val uiState: StateFlow<BoardListUiState> = _uiState

    init {
        loadBoards()
    }

    fun refresh() {
        loadBoards(forceRefresh = true)
    }

    private fun loadBoards(forceRefresh: Boolean = false) {
        _uiState.update { it.copy(isLoading = true, errorMessage = null) }
        viewModelScope.launch {
            val result = getBoardsUseCase(forceRefresh)
            _uiState.update { state ->
                result.fold(
                    onSuccess = { boards ->
                        state.copy(boards = boards, isLoading = false, errorMessage = null)
                    },
                    onFailure = { error ->
                        state.copy(isLoading = false, errorMessage = error.message ?: "")
                    }
                )
            }
        }
    }
}
