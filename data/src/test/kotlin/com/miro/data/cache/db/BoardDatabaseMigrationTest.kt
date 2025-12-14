package com.miro.data.cache.db

import android.content.Context
import androidx.room.Room
import androidx.sqlite.db.SupportSQLiteOpenHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.core.app.ApplicationProvider
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.robolectric.annotation.Config
import org.robolectric.junit5.RobolectricExtension

@ExtendWith(RobolectricExtension::class)
@Config(manifest = Config.NONE, sdk = [34])
class BoardDatabaseMigrationTest {
    private val context: Context = ApplicationProvider.getApplicationContext()
    private val dbName = "board-migration-test.db"

    @BeforeEach
    fun clean() {
        context.deleteDatabase(dbName)
    }

    @AfterEach
    fun tearDown() {
        context.deleteDatabase(dbName)
    }

    @Test
    fun migrate1To2_addsPendingSyncAndKeepsBoards() = runBlocking {
        createVersion1Database(context, dbName)

        val database = Room.databaseBuilder(context, BoardDatabase::class.java, dbName)
            .addMigrations(BoardDatabaseMigrations.MIGRATION_1_2)
            .build()

        database.openHelper.writableDatabase.close()

        val boards = database.boardDao().loadBoards()
        assertEquals(1, boards.size)
        assertEquals("1", boards.first().id)

        database.openHelper.writableDatabase.query("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_sync'").use {
            assertTrue(it.count == 1)
        }

        database.close()
    }

    private fun createVersion1Database(context: Context, name: String) {
        val config = SupportSQLiteOpenHelper.Configuration.builder(context)
            .name(name)
            .callback(object : SupportSQLiteOpenHelper.Callback(1) {
                override fun onCreate(db: androidx.sqlite.db.SupportSQLiteDatabase) {
                    db.execSQL(
                        """
                        CREATE TABLE IF NOT EXISTS boards (
                            id TEXT NOT NULL,
                            name TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            attachments_version INTEGER NOT NULL,
                            PRIMARY KEY(id)
                        )
                        """.trimIndent(),
                    )
                    db.execSQL(
                        """
                        INSERT INTO boards (id, name, updated_at, attachments_version)
                        VALUES ('1', 'Legacy Board', '2024-01-01T00:00:00Z', 0)
                        """.trimIndent(),
                    )
                }

                override fun onUpgrade(db: androidx.sqlite.db.SupportSQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit
            })
            .build()

        FrameworkSQLiteOpenHelperFactory().create(config).apply {
            writableDatabase.close()
            close()
        }
    }
}
