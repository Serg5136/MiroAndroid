package com.miro.data.storage

sealed class StoragePermission {
    data class Scoped(val allowed: Boolean) : StoragePermission()
    data class ReadExternal(val granted: Boolean) : StoragePermission()
    data class WriteExternal(val granted: Boolean) : StoragePermission()

    val isGranted: Boolean
        get() = when (this) {
            is Scoped -> allowed
            is ReadExternal -> granted
            is WriteExternal -> granted
        }
}
