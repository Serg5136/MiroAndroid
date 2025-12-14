package com.miro.data.cache.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface BoardDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertBoards(entities: List<BoardEntity>)

    @Query("SELECT * FROM boards ORDER BY id")
    suspend fun loadBoards(): List<BoardEntity>

    @Query("DELETE FROM pending_sync")
    suspend fun clearPendingSync()

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertPendingSync(entities: List<PendingSyncEntity>)

    @Query("SELECT * FROM pending_sync ORDER BY enqueued_at")
    suspend fun loadPendingSync(): List<PendingSyncEntity>
}
