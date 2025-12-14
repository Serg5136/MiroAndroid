package com.miro.data.cache.db

import android.content.Context
import androidx.room.Room
import androidx.room.RoomDatabase
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption

class BoardDatabaseProvider(private val context: Context) {
    private val databasePath: Path by lazy {
        context.getDatabasePath(BoardDatabase.DATABASE_NAME).toPath()
    }

    fun createDatabase(): BoardDatabase = Room.databaseBuilder(
        context,
        BoardDatabase::class.java,
        BoardDatabase.DATABASE_NAME,
    )
        .addMigrations(*BoardDatabaseMigrations.ALL_MIGRATIONS)
        .setJournalMode(RoomDatabase.JournalMode.TRUNCATE)
        .build()

    fun backup(destinationDir: Path, database: BoardDatabase): Path {
        Files.createDirectories(destinationDir)
        checkpoint(database)
        val target = destinationDir.resolve(BoardDatabase.DATABASE_NAME)
        return Files.copy(databasePath, target, StandardCopyOption.REPLACE_EXISTING)
    }

    fun restore(backupFile: Path) {
        Files.createDirectories(databasePath.parent)
        Files.copy(backupFile, databasePath, StandardCopyOption.REPLACE_EXISTING)
    }

    private fun checkpoint(database: BoardDatabase) {
        val db = database.openHelper.writableDatabase
        db.query("PRAGMA wal_checkpoint(FULL)").use { }
        db.query("PRAGMA optimize").use { }
    }
}
