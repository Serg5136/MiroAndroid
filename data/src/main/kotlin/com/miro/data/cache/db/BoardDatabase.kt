package com.miro.data.cache.db

import androidx.room.Database
import androidx.room.RoomDatabase

/**
 * Room-backed cache for board metadata.
 *
 * Schema history:
 * - version 1: introduces the [BoardEntity] table for cached boards.
 * - version 2: adds [PendingSyncEntity] to track boards awaiting sync requests.
 */
@Database(
    entities = [BoardEntity::class, PendingSyncEntity::class],
    version = 2,
    exportSchema = true,
)
abstract class BoardDatabase : RoomDatabase() {
    abstract fun boardDao(): BoardDao

    companion object {
        const val DATABASE_NAME = "board_cache.db"
    }
}
