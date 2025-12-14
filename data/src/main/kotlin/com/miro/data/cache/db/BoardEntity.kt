package com.miro.data.cache.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "boards")
data class BoardEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,
    @ColumnInfo(name = "name")
    val name: String,
    @ColumnInfo(name = "updated_at")
    val updatedAt: String,
    @ColumnInfo(name = "attachments_version")
    val attachmentsVersion: Long,
)

@Entity(tableName = "pending_sync")
data class PendingSyncEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,
    @ColumnInfo(name = "name")
    val name: String,
    @ColumnInfo(name = "updated_at")
    val updatedAt: String,
    @ColumnInfo(name = "attachments_version")
    val attachmentsVersion: Long,
    @ColumnInfo(name = "enqueued_at")
    val enqueuedAt: Long,
)
