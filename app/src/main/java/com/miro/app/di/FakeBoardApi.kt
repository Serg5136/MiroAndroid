package com.miro.app.di

import com.miro.data.network.BoardApi
import com.miro.data.network.BoardPayload
import com.miro.data.network.SyncPayload
import kotlinx.coroutines.delay
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.util.concurrent.ConcurrentHashMap

class FakeBoardApi : BoardApi {
    private val boards = ConcurrentHashMap<String, BoardPayload>()

    init {
        val formatter = DateTimeFormatter.ISO_OFFSET_DATE_TIME
        repeat(3) { index ->
            val id = (index + 1).toString()
            boards[id] = BoardPayload(
                id = id,
                name = "Board $id",
                updatedAt = OffsetDateTime.now().minusDays(index.toLong()).format(formatter),
                attachmentsVersion = index.toLong(),
            )
        }
    }

    override suspend fun getBoards(): List<BoardPayload> {
        delay(300)
        return boards.values.sortedBy { it.id }
    }

    override suspend fun getBoard(id: String): BoardPayload {
        delay(150)
        return boards[id] ?: error("Board not found")
    }

    override suspend fun pushBoards(payload: SyncPayload) {
        payload.boards.forEach { boards[it.id] = it }
    }
}
