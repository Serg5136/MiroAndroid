package dev.miro.core

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

const val SCHEMA_VERSION = 5
val SUPPORTED_SCHEMA_VERSIONS = setOf(1, 2, 3, 4, SCHEMA_VERSION)

@Serializable
data class Attachment(
    val id: Int,
    val name: String,
    @SerialName("source_type") val sourceType: String,
    @SerialName("mime_type") val mimeType: String,
    val width: Int,
    val height: Int,
    @SerialName("offset_x") var offsetX: Double = 0.0,
    @SerialName("offset_y") var offsetY: Double = 0.0,
    @SerialName("preview_scale") var previewScale: Double = 1.0,
    @SerialName("storage_path") var storagePath: String? = null,
    @SerialName("data_base64") var dataBase64: String? = null,
)

@Serializable
data class Card(
    val id: Int,
    var x: Double,
    var y: Double,
    var width: Double,
    var height: Double,
    var text: String = "",
    var color: String = "#fff9b1",
    val attachments: MutableList<Attachment> = mutableListOf(),
)

fun bulkUpdateCardColors(
    cards: MutableMap<Int, Card>,
    cardIds: Iterable<Int>,
    color: String,
): List<Int> {
    val updated = mutableListOf<Int>()
    cardIds.forEach { id ->
        val card = cards[id] ?: return@forEach
        if (card.color != color) {
            card.color = color
            updated += id
        }
    }
    return updated
}

const val DEFAULT_CONNECTION_DIRECTION = "end"
const val DEFAULT_CONNECTION_STYLE = "straight"
const val DEFAULT_CONNECTION_RADIUS = 0.0
const val DEFAULT_CONNECTION_CURVATURE = 0.0
val VALID_CONNECTION_DIRECTIONS = setOf("start", "end")
val VALID_CONNECTION_STYLES = setOf("straight", "rounded", "elbow")

@Serializable
data class Connection(
    @SerialName("from") val fromId: Int,
    @SerialName("to") val toId: Int,
    var label: String = "",
    var direction: String = DEFAULT_CONNECTION_DIRECTION,
    var style: String = DEFAULT_CONNECTION_STYLE,
    var radius: Double = DEFAULT_CONNECTION_RADIUS,
    var curvature: Double = DEFAULT_CONNECTION_CURVATURE,
    @SerialName("from_anchor") var fromAnchor: String? = null,
    @SerialName("to_anchor") var toAnchor: String? = null,
) {
    init {
        direction = normalizeDirection(direction)
        style = normalizeStyle(style)
        radius = normalizeFloat(radius, DEFAULT_CONNECTION_RADIUS)
        curvature = normalizeFloat(curvature, DEFAULT_CONNECTION_CURVATURE)
    }

    fun toggleDirection() {
        direction = if (direction == "end") "start" else "end"
    }

    companion object {
        private fun normalizeDirection(direction: String?): String =
            direction?.takeIf { VALID_CONNECTION_DIRECTIONS.contains(it) }
                ?: DEFAULT_CONNECTION_DIRECTION

        private fun normalizeStyle(style: String?): String =
            style?.takeIf { VALID_CONNECTION_STYLES.contains(it) } ?: DEFAULT_CONNECTION_STYLE

        private fun normalizeFloat(value: Any?, default: Double): Double =
            when (value) {
                null -> default
                is Number -> value.toDouble()
                else -> value.toString().toDoubleOrNull() ?: default
            }

        fun fromPayload(payload: Connection): Connection =
            Connection(
                fromId = payload.fromId,
                toId = payload.toId,
                label = payload.label,
                direction = normalizeDirection(payload.direction),
                style = normalizeStyle(payload.style),
                radius = normalizeFloat(payload.radius, DEFAULT_CONNECTION_RADIUS),
                curvature = normalizeFloat(payload.curvature, DEFAULT_CONNECTION_CURVATURE),
                fromAnchor = payload.fromAnchor,
                toAnchor = payload.toAnchor,
            )
    }
}

@Serializable
data class Frame(
    val id: Int,
    val x1: Double,
    val y1: Double,
    val x2: Double,
    val y2: Double,
    var title: String = "Группа",
    var collapsed: Boolean = false,
)

@Serializable
private data class BoardPayload(
    @SerialName("schema_version") val schemaVersion: Int = SCHEMA_VERSION,
    val cards: List<Card>,
    val connections: List<Connection>,
    val frames: List<Frame>,
)

data class BoardData(
    val cards: MutableMap<Int, Card>,
    val connections: MutableList<Connection>,
    val frames: MutableMap<Int, Frame>,
) {
    fun toJson(json: Json = DEFAULT_JSON): String =
        json.encodeToString(BoardPayload.serializer(), toPayload())

    fun toPayload(): BoardPayload = BoardPayload(
        cards = cards.values.toList(),
        connections = connections.toList(),
        frames = frames.values.toList(),
    )

    companion object {
        fun fromJson(content: String, json: Json = DEFAULT_JSON): BoardData {
            val payload = json.decodeFromString(BoardPayload.serializer(), content)
            return fromPayload(payload)
        }

        fun fromPayload(payload: BoardPayload): BoardData {
            val cards = payload.cards.associateBy { it.id }.toMutableMap()
            val connections = payload.connections.mapNotNull {
                runCatching { Connection.fromPayload(it) }.getOrNull()
            }.toMutableList()
            val frames = payload.frames.associateBy { it.id }.toMutableMap()
            return BoardData(cards = cards, connections = connections, frames = frames)
        }
    }
}

val DEFAULT_JSON: Json = Json {
    prettyPrint = true
    encodeDefaults = true
    ignoreUnknownKeys = true
}
