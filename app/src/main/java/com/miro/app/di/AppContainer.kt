package com.miro.app.di

import android.content.Context
import com.miro.app.domain.usecase.GetBoardDetailUseCase
import com.miro.app.domain.usecase.GetBoardsUseCase
import com.miro.data.cache.DataStoreSettings
import com.miro.data.cache.InMemoryRoomCache
import com.miro.data.cache.RoomCache
import com.miro.data.repository.BoardRepository
import com.miro.data.storage.ScopedStorageManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import java.io.File
import kotlin.io.path.Path

class AppContainer(context: Context) {
    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val cache: RoomCache = InMemoryRoomCache()
    private val settings = DataStoreSettings(
        name = "mini-miro",
        scope = appScope,
        directory = context.dataDir.toPath(),
    )
    private val storage = ScopedStorageManager(
        root = Path(File(context.filesDir, "attachments").absolutePath),
    )

    private val api = FakeBoardApi()
    private val repository = BoardRepository(
        api = api,
        cache = cache,
        settings = settings,
        storage = storage,
    )

    val getBoardsUseCase = GetBoardsUseCase(repository)
    val getBoardDetailUseCase = GetBoardDetailUseCase(repository)
}
