package dev.miro.core

import io.mockk.every
import io.mockk.mockk
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class BoardModelsTest {
    @Test
    fun `toJson uses provided Json instance`() {
        val board = BoardData(
            cards = mutableMapOf(1 to Card(id = 1, x = 0.0, y = 0.0, width = 100.0, height = 50.0)),
            connections = mutableListOf(),
            frames = mutableMapOf(),
        )

        val customJson = mockk<Json>()
        every { customJson.encodeToString(BoardPayload.serializer(), any()) } returns "custom-json"

        assertEquals("custom-json", board.toJson(customJson))
    }

    @Test
    fun `round trip serializes board data with connections and frames`() {
        val board = BoardData(
            cards = mutableMapOf(
                1 to Card(
                    id = 1,
                    x = 10.0,
                    y = 20.0,
                    width = 150.0,
                    height = 80.0,
                    text = "Task",
                    color = "#abc",
                    attachments = mutableListOf(
                        Attachment(
                            id = 1,
                            name = "pic.png",
                            sourceType = "clipboard",
                            mimeType = "image/png",
                            width = 100,
                            height = 50,
                            storagePath = "attachments/1-1.png",
                            dataBase64 = null,
                        )
                    ),
                )
            ),
            connections = mutableListOf(
                Connection(
                    fromId = 1,
                    toId = 2,
                    label = "Edge",
                    direction = "start",
                    style = "rounded",
                    radius = 12.0,
                    curvature = 1.5,
                )
            ),
            frames = mutableMapOf(
                5 to Frame(
                    id = 5,
                    x1 = 0.0,
                    y1 = 0.0,
                    x2 = 200.0,
                    y2 = 100.0,
                    title = "Frame",
                    collapsed = false,
                )
            ),
        )

        val restored = BoardData.fromJson(board.toJson())
        assertEquals(board.cards.keys, restored.cards.keys)
        assertEquals(board.connections.first().direction, restored.connections.first().direction)
        assertEquals(board.frames[5]?.title, restored.frames[5]?.title)
        assertEquals(board.cards[1]?.attachments?.first()?.storagePath, restored.cards[1]?.attachments?.first()?.storagePath)
    }

    @Test
    fun `bulkUpdateCardColors changes only requested cards`() {
        val cards = mutableMapOf(
            1 to Card(1, 0.0, 0.0, 10.0, 10.0, color = "#fff9b1"),
            2 to Card(2, 0.0, 0.0, 10.0, 10.0, color = "#ff0000"),
        )
        val updated = bulkUpdateCardColors(cards, listOf(1, 2, 3), "#00ff00")

        assertEquals(listOf(1, 2), updated)
        assertTrue(cards.values.all { it.color == "#00ff00" || it.id == 3 })
    }
}
