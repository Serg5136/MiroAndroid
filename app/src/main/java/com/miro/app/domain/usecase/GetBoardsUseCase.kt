package com.miro.app.domain.usecase

import com.miro.app.domain.model.BoardSummary
import com.miro.data.repository.BoardRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class GetBoardsUseCase(private val repository: BoardRepository) {
    suspend operator fun invoke(forceRefresh: Boolean = false): Result<List<BoardSummary>> =
        withContext(Dispatchers.IO) {
            runCatching {
                repository.getBoards(forceRefresh).map { payload ->
                    BoardSummary(
                        id = payload.id,
                        name = payload.name,
                        updatedAt = payload.updatedAt,
                    )
                }
            }
        }
}
