package com.miro.app.push

import android.app.PendingIntent
import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.miro.app.MainActivity
import com.miro.app.MiniMiroApp
import com.miro.app.R
import com.miro.app.analytics.AnalyticsLogger

class MiroMessagingService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        Log.d(TAG, "FCM registration token refreshed: $token")
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val boardId = remoteMessage.data[BOARD_ID_KEY]
        AnalyticsLogger.logNotificationReceived(remoteMessage.messageId, boardId)

        val launchIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            boardId?.let { data = Uri.parse("https://mini-miro.app/board/$it") }
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            boardId?.hashCode() ?: 0,
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(this, MiniMiroApp.DEFAULT_PUSH_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(remoteMessage.notification?.title ?: getString(R.string.app_name))
            .setContentText(remoteMessage.notification?.body ?: getString(R.string.push_default_body))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        val notificationId = boardId?.hashCode() ?: remoteMessage.messageId?.hashCode() ?: 0
        NotificationManagerCompat.from(this).notify(notificationId, notification)
    }

    companion object {
        private const val TAG = "MiroMessagingService"
        private const val BOARD_ID_KEY = "boardId"
    }
}
