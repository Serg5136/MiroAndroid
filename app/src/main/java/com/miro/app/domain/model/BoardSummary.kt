package com.miro.app.domain.model

import java.io.Serializable

data class BoardSummary(
    val id: String,
    val name: String,
    val updatedAt: String,
) : Serializable
