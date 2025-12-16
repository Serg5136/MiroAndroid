package com.miro.data.repository

import com.miro.data.cache.RoomCache
import com.miro.data.cache.DataStoreSettings
import com.miro.data.network.BoardApi
import com.miro.data.network.BoardPayload
import com.miro.data.network.SyncPayload
import com.miro.data.storage.ScopedStorageManager
import com.miro.data.background.OfflineRetryPolicy
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import kotlinx.coroutines.delay
import kotlin.time.Duration.Companion.milliseconds

class BoardRepository(
    private val api: BoardApi,
    private val cache: RoomCache,
    private val settings: DataStoreSettings,
    private val storage: ScopedStorageManager,
    private val retryPolicy: OfflineRetryPolicy = OfflineRetryPolicy(),
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {

    suspend fun getBoards(forceRefresh: Boolean = false): List<BoardPayload> = withContext(ioDispatcher) {
        val cached = cache.getBoards()
        if (cached.isNotEmpty() && !forceRefresh) return@withContext cached

        val result = retryWithBackoff { api.getBoards() }
            .onSuccess { cache.saveBoards(it) }
        if (result.isSuccess) {
            settings.setNetworkOffline(false)
        } else {
            settings.setNetworkOffline(true)
        }
        return@withContext result.getOrDefault(cached)
    }

    suspend fun getBoard(id: String, forceRefresh: Boolean = false): BoardPayload? = withContext(ioDispatcher) {
        val cached = cache.getBoards().firstOrNull { it.id == id }
        if (cached != null && !forceRefresh) return@withContext cached

        val result = retryWithBackoff { api.getBoard(id) }
            .onSuccess { cache.saveBoards(listOf(it)) }
        if (result.isSuccess) {
            settings.setNetworkOffline(false)
        }
        return@withContext result.getOrNull() ?: cached
    }

    suspend fun pushBoards(localBoards: List<BoardPayload>) = withContext(ioDispatcher) {
        if (localBoards.isEmpty()) return@withContext
        cache.markPendingSync(localBoards)
        val payload = SyncPayload(localBoards)
        runCatching { api.pushBoards(payload) }
            .onSuccess { cache.saveBoards(localBoards) }
            .onSuccess { settings.setNetworkOffline(false) }
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

    private suspend fun <T> retryWithBackoff(operation: suspend () -> T): Result<T> {
        var delayDuration = retryPolicy.initialDelay
        var lastResult: Result<T> = runCatching { operation() }
        repeat(retryPolicy.maxAttempts - 1) {
            if (lastResult.isSuccess) return lastResult
            delay(delayDuration.inWholeMilliseconds)
            delayDuration = (delayDuration.inWholeMilliseconds * retryPolicy.multiplier).milliseconds
            lastResult = runCatching { operation() }
        }
        return lastResult
    }
}
