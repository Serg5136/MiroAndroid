package com.miro.data.storage

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.io.path.inputStream
import kotlin.io.path.outputStream

class ScopedStorageManager(
    private val root: Path,
    private val scopedPermission: StoragePermission = StoragePermission.Scoped(true),
    private val readPermission: StoragePermission = StoragePermission.ReadExternal(true),
    private val writePermission: StoragePermission = StoragePermission.WriteExternal(true),
) {
    init {
        if (!root.toFile().exists()) {
            Files.createDirectories(root)
        }
    }

    fun canRead(): Boolean = scopedPermission.isGranted && readPermission.isGranted
    fun canWrite(): Boolean = scopedPermission.isGranted && writePermission.isGranted

    fun writeAttachment(id: String, bytes: ByteArray): Path {
        require(canWrite()) { "Write permission is not granted for scoped storage" }
        val path = root.resolve("$id.bin")
        path.outputStream().use { it.write(bytes) }
        return path
    }

    fun readAttachment(id: String): ByteArray? {
        if (!canRead()) return null
        val path = root.resolve("$id.bin")
        if (!path.exists()) return null
        return path.inputStream().use { it.readBytes() }
    }

    fun removeAttachment(id: String) {
        if (!canWrite()) return
        Files.deleteIfExists(root.resolve("$id.bin"))
    }
}
