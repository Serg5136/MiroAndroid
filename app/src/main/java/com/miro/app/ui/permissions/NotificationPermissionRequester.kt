package com.miro.app.ui.permissions

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.miro.app.R
import com.miro.app.analytics.AnalyticsLogger

@Composable
fun NotificationPermissionRequester(
    onPermissionResult: (Boolean) -> Unit = {},
) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
        LaunchedEffect(Unit) { onPermissionResult(true) }
        return
    }

    val activity = LocalContext.current as? Activity ?: return
    var permissionGranted by rememberSaveable {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                activity,
                Manifest.permission.POST_NOTIFICATIONS,
            ) == PackageManager.PERMISSION_GRANTED
        )
    }
    var showRationale by rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(permissionGranted) {
        if (permissionGranted) {
            onPermissionResult(true)
        }
    }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
    ) { granted ->
        permissionGranted = granted
        onPermissionResult(granted)
        AnalyticsLogger.logPermissionResult(
            permission = Manifest.permission.POST_NOTIFICATIONS,
            granted = granted,
            rationaleShown = showRationale,
        )
    }

    LaunchedEffect(permissionGranted, showRationale) {
        if (!permissionGranted) {
            if (ActivityCompat.shouldShowRequestPermissionRationale(
                    activity,
                    Manifest.permission.POST_NOTIFICATIONS,
                )
            ) {
                showRationale = true
            } else if (!showRationale) {
                launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    if (showRationale && !permissionGranted) {
        NotificationPermissionRationale(
            onConfirm = {
                showRationale = false
                launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
            },
            onDismiss = {
                showRationale = false
                onPermissionResult(false)
                AnalyticsLogger.logPermissionResult(
                    permission = Manifest.permission.POST_NOTIFICATIONS,
                    granted = false,
                    rationaleShown = true,
                )
            },
        )
    }
}

@Composable
private fun NotificationPermissionRationale(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(text = LocalContext.current.getString(R.string.notification_permission_title)) },
        text = { Text(text = LocalContext.current.getString(R.string.notification_permission_message)) },
        confirmButton = {
            TextButton(onClick = onConfirm) {
                Text(text = LocalContext.current.getString(R.string.allow))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(text = LocalContext.current.getString(R.string.not_now))
            }
        },
    )
}
