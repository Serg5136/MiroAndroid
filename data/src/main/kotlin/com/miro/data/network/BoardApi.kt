package com.miro.data.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

@Serializable
data class BoardPayload(
    @SerialName("id") val id: String,
    @SerialName("name") val name: String,
    @SerialName("updated_at") val updatedAt: String,
    @SerialName("attachments_version") val attachmentsVersion: Long,
)

@Serializable
data class SyncPayload(
    @SerialName("boards") val boards: List<BoardPayload>
)

interface BoardApi {
    @GET("boards")
    suspend fun getBoards(): List<BoardPayload>

    @GET("boards/{id}")
    suspend fun getBoard(@Path("id") id: String): BoardPayload

    @POST("boards/sync")
    suspend fun pushBoards(@Body payload: SyncPayload)
}
