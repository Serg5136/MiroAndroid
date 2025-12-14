package com.miro.data.background

import kotlin.time.Duration
import kotlin.time.Duration.Companion.seconds

data class OfflineRetryPolicy(
    val maxAttempts: Int = 3,
    val initialDelay: Duration = 5.seconds,
    val multiplier: Double = 2.0,
)
