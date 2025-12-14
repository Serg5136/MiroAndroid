package com.miro.data.cache

import androidx.datastore.core.DataStore
import androidx.datastore.core.handlers.ReplaceFileCorruptionHandler
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.preferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.nio.file.Path

class DataStoreSettings(
    name: String,
    scope: CoroutineScope,
    directory: Path,
) {
    private val dataStore: DataStore<Preferences> = PreferenceDataStoreFactory.createWithPath(
        corruptionHandler = ReplaceFileCorruptionHandler { emptyPreferences() },
        scope = scope,
        produceFile = { directory.resolve("${name}.preferences") }
    )

    val syncState: Flow<String?> = dataStore.data.map { prefs -> prefs[preferencesKey("sync_state")] }

    suspend fun setLastSynced(version: Long) {
        dataStore.edit { prefs ->
            prefs[longPreferencesKey("last_synced")] = version
        }
    }

    suspend fun setNetworkOffline(isOffline: Boolean) {
        dataStore.edit { prefs ->
            prefs[booleanPreferencesKey("network_offline")] = isOffline
        }
    }

    suspend fun updateScopedStorageHint(shown: Boolean) {
        dataStore.edit { prefs ->
            prefs[intPreferencesKey("scoped_storage_hint")] = if (shown) 1 else 0
        }
    }
}
