package com.miro.data.repository

import com.miro.data.cache.RoomCache
import com.miro.data.cache.DataStoreSettings
import com.miro.data.network.BoardApi
import com.miro.data.network.BoardPayload
import com.miro.data.network.SyncPayload
import com.miro.data.storage.ScopedStorageManager
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext

class BoardRepository(
    private val api: BoardApi,
    private val cache: RoomCache,
    private val settings: DataStoreSettings,
    private val storage: ScopedStorageManager,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {

    suspend fun getBoards(forceRefresh: Boolean = false): List<BoardPayload> = withContext(ioDispatcher) {
        val cached = cache.getBoards()
        if (cached.isNotEmpty() && !forceRefresh) return@withContext cached

        return@withContext runCatching { api.getBoards() }
            .onSuccess { cache.saveBoards(it) }
            .getOrDefault(cached)
    }

    suspend fun pushBoards(localBoards: List<BoardPayload>) = withContext(ioDispatcher) {
        if (localBoards.isEmpty()) return@withContext
        cache.markPendingSync(localBoards)
        val payload = SyncPayload(localBoards)
        runCatching { api.pushBoards(payload) }
            .onSuccess { cache.saveBoards(localBoards) }
            .onFailure { settings.setNetworkOffline(true) }
    }

    suspend fun retryPendingSync(): Boolean = withContext(ioDispatcher) {
        val pending = cache.pendingSync()
        if (pending.isEmpty()) return@withContext false

        return@withContext runCatching {
            api.pushBoards(SyncPayload(pending))
        }.isSuccess
    }

    suspend fun writeAttachment(id: String, bytes: ByteArray) = withContext(ioDispatcher) {
        storage.writeAttachment(id, bytes)
    }

    suspend fun readAttachment(id: String): ByteArray? = withContext(ioDispatcher) {
        storage.readAttachment(id)
    }
}
