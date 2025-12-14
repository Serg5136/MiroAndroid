package com.miro.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.google.firebase.FirebaseApp
import com.google.firebase.analytics.ktx.analytics
import com.google.firebase.crashlytics.ktx.crashlytics
import com.google.firebase.ktx.Firebase
import com.google.firebase.messaging.ktx.messaging

class MiniMiroApp : Application() {
    override fun onCreate() {
        super.onCreate()
        FirebaseApp.initializeApp(this)
        configureAnalytics()
        configureCrashlytics()
        configureMessaging()
        createDefaultNotificationChannel()
    }

    private fun configureAnalytics() {
        Firebase.analytics.setAnalyticsCollectionEnabled(!BuildConfig.DEBUG)
    }

    private fun configureCrashlytics() {
        Firebase.crashlytics.setCrashlyticsCollectionEnabled(!BuildConfig.DEBUG)
    }

    private fun configureMessaging() {
        Firebase.messaging.isAutoInitEnabled = true
    }

    private fun createDefaultNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                DEFAULT_PUSH_CHANNEL_ID,
                getString(R.string.push_channel_name),
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = getString(R.string.push_channel_description)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    companion object {
        const val DEFAULT_PUSH_CHANNEL_ID = "miro_push"
    }
}
