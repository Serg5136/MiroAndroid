package com.miro.app.analytics

import android.os.Bundle
import com.google.firebase.analytics.ktx.analytics
import com.google.firebase.analytics.ktx.logEvent
import com.google.firebase.ktx.Firebase

object AnalyticsLogger {
    private val analytics get() = Firebase.analytics

    fun logPermissionResult(permission: String, granted: Boolean, rationaleShown: Boolean) {
        analytics.logEvent("permission_result") {
            param("permission", permission)
            param("granted", granted.toString())
            param("rationale_shown", rationaleShown.toString())
        }
    }

    fun logNotificationReceived(messageId: String?, boardId: String?) {
        val params = Bundle().apply {
            messageId?.let { putString("message_id", it) }
            boardId?.let { putString("board_id", it) }
        }
        analytics.logEvent("push_received", params)
    }

    fun logNotificationTapped(boardId: String?) {
        analytics.logEvent("push_open") {
            boardId?.let { param("board_id", it) }
        }
    }
}
