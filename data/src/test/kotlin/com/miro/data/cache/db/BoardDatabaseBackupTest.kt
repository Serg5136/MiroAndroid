package com.miro.data.cache.db

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.robolectric.annotation.Config
import org.robolectric.junit5.RobolectricExtension
import java.nio.file.Files
import java.time.Instant

@ExtendWith(RobolectricExtension::class)
@Config(manifest = Config.NONE, sdk = [34])
class BoardDatabaseBackupTest {
    private val context: Context = ApplicationProvider.getApplicationContext()
    private val provider = BoardDatabaseProvider(context)
    private var database: BoardDatabase? = null

    @BeforeEach
    fun setUp() {
        context.deleteDatabase(BoardDatabase.DATABASE_NAME)
        database = provider.createDatabase()
    }

    @AfterEach
    fun tearDown() {
        database?.close()
        context.deleteDatabase(BoardDatabase.DATABASE_NAME)
    }

    @Test
    fun backupAndRestoreCopiesCache() = runBlocking {
        val dao = requireNotNull(database).boardDao()
        dao.upsertBoards(
            listOf(
                BoardEntity(
                    id = "42",
                    name = "Backup Board",
                    updatedAt = Instant.EPOCH.toString(),
                    attachmentsVersion = 7,
                ),
            ),
        )

        val tempDir = Files.createTempDirectory("board-db-backup")
        val backupFile = provider.backup(tempDir, requireNotNull(database))

        database?.close()
        context.deleteDatabase(BoardDatabase.DATABASE_NAME)
        provider.restore(backupFile)
        database = provider.createDatabase()

        val restoredBoards = requireNotNull(database).boardDao().loadBoards()
        assertEquals(1, restoredBoards.size)
        assertEquals("Backup Board", restoredBoards.first().name)
    }
}
