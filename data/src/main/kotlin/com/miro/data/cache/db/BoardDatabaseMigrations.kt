package com.miro.data.cache.db

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

object BoardDatabaseMigrations {
    val MIGRATION_1_2 = object : Migration(1, 2) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL(
                """
                CREATE TABLE IF NOT EXISTS pending_sync (
                    id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    attachments_version INTEGER NOT NULL,
                    enqueued_at INTEGER NOT NULL,
                    PRIMARY KEY(id)
                )
                """.trimIndent(),
            )
        }
    }

    val ALL_MIGRATIONS = arrayOf(MIGRATION_1_2)
}
