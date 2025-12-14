package com.miro.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.miro.app.domain.model.BoardSummary
import com.miro.app.ui.BoardListUiState
import com.miro.app.ui.theme.MiniMiroTheme
import com.miro.app.R
import androidx.compose.ui.res.stringResource

@Composable
fun BoardListRoute(
    state: BoardListUiState,
    onRefresh: () -> Unit,
    onBoardClick: (String) -> Unit,
) {
    BoardListScreen(
        state = state,
        onBoardClick = onBoardClick,
        onRefresh = onRefresh,
    )
}

@Composable
fun BoardListScreen(
    state: BoardListUiState,
    onBoardClick: (String) -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
) {
    MiniMiroTheme {
        Scaffold(
            modifier = modifier,
            topBar = {
                TopAppBar(
                    title = { Text(text = stringResource(id = R.string.board_list_title)) },
                    actions = {
                        FilledIconButton(
                            onClick = onRefresh,
                            modifier = Modifier.semantics {
                                contentDescription = stringResource(R.string.refresh)
                            }
                        ) {
                            androidx.compose.material3.Icon(
                                imageVector = Icons.Default.Refresh,
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
            Box(modifier = Modifier.padding(innerPadding).fillMaxSize()) {
                when {
                    state.isLoading -> LoadingState()
                    state.errorMessage != null -> ErrorState(
                        message = state.errorMessage,
                        onRetry = onRefresh
                    )
                    else -> BoardList(
                        boards = state.boards,
                        onBoardClick = onBoardClick,
                    )
                }
            }
        }
    }
}

@Composable
private fun BoardList(
    boards: List<BoardSummary>,
    onBoardClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(boards, key = { it.id }) { board ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .semantics {
                        contentDescription = stringResource(R.string.board_item_cd, board.name)
                    },
                onClick = { onBoardClick(board.id) }
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = board.name,
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = stringResource(R.string.last_updated, board.updatedAt),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
    }
}

@Composable
private fun LoadingState() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .semantics { contentDescription = stringResource(R.string.loading_description) },
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CircularProgressIndicator()
        Text(
            text = stringResource(R.string.loading),
            modifier = Modifier.padding(top = 8.dp)
        )
    }
}

@Composable
private fun ErrorState(
    message: String,
    onRetry: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
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
