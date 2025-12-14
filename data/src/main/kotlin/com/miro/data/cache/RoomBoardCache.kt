package com.miro.data.cache

import com.miro.data.cache.db.BoardDao
import com.miro.data.cache.db.BoardEntity
import com.miro.data.cache.db.PendingSyncEntity
import com.miro.data.network.BoardPayload
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Clock

class RoomBoardCache(
    private val dao: BoardDao,
    private val clock: Clock = Clock.systemUTC(),
) : RoomCache {

    override suspend fun saveBoards(items: List<BoardPayload>) = withContext(Dispatchers.IO) {
        dao.upsertBoards(items.map(BoardPayload::toEntity))
    }

    override suspend fun getBoards(): List<BoardPayload> = withContext(Dispatchers.IO) {
        dao.loadBoards().map(BoardEntity::toPayload)
    }

    override suspend fun markPendingSync(items: List<BoardPayload>) = withContext(Dispatchers.IO) {
        val now = clock.millis()
        val pendingEntities = items.map { it.toPendingEntity(now) }
        dao.clearPendingSync()
        dao.upsertPendingSync(pendingEntities)
    }

    override suspend fun pendingSync(): List<BoardPayload> = withContext(Dispatchers.IO) {
        dao.loadPendingSync().map(PendingSyncEntity::toPayload)
    }
}

private fun BoardPayload.toEntity(): BoardEntity = BoardEntity(
    id = id,
    name = name,
    updatedAt = updatedAt,
    attachmentsVersion = attachmentsVersion,
)

private fun BoardPayload.toPendingEntity(enqueuedAt: Long): PendingSyncEntity = PendingSyncEntity(
    id = id,
    name = name,
    updatedAt = updatedAt,
    attachmentsVersion = attachmentsVersion,
    enqueuedAt = enqueuedAt,
)

private fun BoardEntity.toPayload(): BoardPayload = BoardPayload(
    id = id,
    name = name,
    updatedAt = updatedAt,
    attachmentsVersion = attachmentsVersion,
)

private fun PendingSyncEntity.toPayload(): BoardPayload = BoardPayload(
    id = id,
    name = name,
    updatedAt = updatedAt,
    attachmentsVersion = attachmentsVersion,
)
