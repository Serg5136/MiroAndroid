package com.miro.data.background

import com.miro.data.repository.BoardRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.math.pow

class SyncScheduler(
    private val repository: BoardRepository,
    private val service: ForegroundSyncService,
    private val retryPolicy: OfflineRetryPolicy = OfflineRetryPolicy(),
    private val scope: CoroutineScope = CoroutineScope(Dispatchers.IO),
) {
    private val _isRunning = MutableStateFlow(false)
    val isRunning: StateFlow<Boolean> = _isRunning

    private var periodicJob: Job? = null

    fun schedulePeriodicSync(intervalMillis: Long = 15 * 60 * 1000L) {
        periodicJob?.cancel()
        periodicJob = scope.launch {
            while (isActive) {
                runSyncOnce()
                delay(intervalMillis)
            }
        }
    }

    fun triggerRetryableSync() {
        scope.launch { retryWithBackoff() }
    }

    private suspend fun retryWithBackoff() {
        for (attempt in 0 until retryPolicy.maxAttempts) {
            val success = runSyncOnce()
            if (success) return

            val delayValue = (retryPolicy.initialDelay.inWholeMilliseconds * retryPolicy.multiplier.pow(attempt))
                .toLong()
            delay(delayValue)
        }
    }

    private suspend fun runSyncOnce(): Boolean {
        _isRunning.value = true
        service.start("Synchronizing boards…")
        val success = repository.retryPendingSync()
        service.updateProgress(if (success) 100 else 0)
        if (success) {
            service.stop()
        }
        _isRunning.value = false
        return success
    }
}
