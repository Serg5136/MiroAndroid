package com.miro.data.cache

import com.miro.data.network.BoardPayload
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

interface RoomCache {
    suspend fun saveBoards(items: List<BoardPayload>)
    suspend fun getBoards(): List<BoardPayload>
    suspend fun markPendingSync(items: List<BoardPayload>)
    suspend fun pendingSync(): List<BoardPayload>
}

class InMemoryRoomCache : RoomCache {
    private val mutex = Mutex()
    private val boards = mutableMapOf<String, BoardPayload>()
    private val pending = LinkedHashMap<String, BoardPayload>()

    override suspend fun saveBoards(items: List<BoardPayload>) {
        mutex.withLock {
            items.forEach { boards[it.id] = it }
        }
    }

    override suspend fun getBoards(): List<BoardPayload> = mutex.withLock { boards.values.toList() }

    override suspend fun markPendingSync(items: List<BoardPayload>) {
        mutex.withLock {
            items.forEach { pending[it.id] = it }
        }
    }

    override suspend fun pendingSync(): List<BoardPayload> = mutex.withLock { pending.values.toList() }
}
