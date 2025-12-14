package com.miro.data.background

interface ForegroundSyncService {
    fun start(progressMessage: String)
    fun updateProgress(progress: Int)
    fun stop()
}
