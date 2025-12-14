package com.miro.app.domain.usecase

import com.miro.app.domain.model.BoardSummary
import com.miro.data.repository.BoardRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class GetBoardDetailUseCase(private val repository: BoardRepository) {
    suspend operator fun invoke(id: String): Result<BoardSummary> = withContext(Dispatchers.IO) {
        runCatching {
            val payload = repository.getBoard(id) ?: error("Board not found")
            BoardSummary(payload.id, payload.name, payload.updatedAt)
        }
    }
}
