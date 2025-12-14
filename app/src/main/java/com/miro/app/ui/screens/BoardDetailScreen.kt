package com.miro.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.miro.app.R
import com.miro.app.ui.BoardDetailUiState
import com.miro.app.ui.theme.MiniMiroTheme

@Composable
fun BoardDetailRoute(
    state: BoardDetailUiState,
    onRetry: () -> Unit,
    onBack: () -> Unit,
) {
    BoardDetailScreen(
        state = state,
        onBack = onBack,
        onRetry = onRetry,
    )
}

@Composable
fun BoardDetailScreen(
    state: BoardDetailUiState,
    onBack: () -> Unit,
    onRetry: () -> Unit,
) {
    MiniMiroTheme {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(text = stringResource(R.string.board_detail_title)) },
                    navigationIcon = {
                        IconButton(
                            onClick = onBack,
                            modifier = Modifier.semantics {
                                contentDescription = stringResource(R.string.back)
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.ArrowBack,
                                contentDescription = null,
                            )
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                )
            }
        ) { innerPadding ->
            when {
                state.isLoading -> DetailLoading(modifier = Modifier.padding(innerPadding))
                state.errorMessage != null -> DetailError(
                    message = state.errorMessage,
                    onRetry = onRetry,
                    modifier = Modifier.padding(innerPadding),
                )
                state.board != null -> DetailContent(
                    state = state,
                    modifier = Modifier.padding(innerPadding),
                )
            }
        }
    }
}

@Composable
private fun DetailContent(
    state: BoardDetailUiState,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(text = state.board?.name ?: "", style = MaterialTheme.typography.headlineSmall)
        Text(
            text = stringResource(R.string.last_updated, state.board?.updatedAt ?: ""),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun DetailLoading(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .semantics { contentDescription = stringResource(R.string.loading_description) },
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CircularProgressIndicator()
        Text(text = stringResource(R.string.loading), modifier = Modifier.padding(top = 8.dp))
    }
}

@Composable
private fun DetailError(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = stringResource(R.string.error_loading))
        if (message.isNotBlank()) {
            Text(text = message, style = MaterialTheme.typography.bodyMedium)
        }
        Button(onClick = onRetry, modifier = Modifier.padding(top = 8.dp)) {
            Text(text = stringResource(R.string.retry))
        }
    }
}
