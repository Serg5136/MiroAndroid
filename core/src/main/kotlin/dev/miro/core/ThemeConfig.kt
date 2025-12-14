package dev.miro.core

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.decodeFromStream

const val CONFIG_FILENAME = "_mini_miro_config.json"

@Serializable
data class ThemePalette(
    val bg: String,
    val grid: String,
    @SerialName("card_default") val cardDefault: String,
    @SerialName("card_outline") val cardOutline: String,
    @SerialName("frame_bg") val frameBg: String,
    @SerialName("frame_outline") val frameOutline: String,
    @SerialName("frame_collapsed_bg") val frameCollapsedBg: String,
    @SerialName("frame_collapsed_outline") val frameCollapsedOutline: String,
    val text: String,
    val connection: String,
    @SerialName("connection_label") val connectionLabel: String,
    @SerialName("minimap_bg") val minimapBg: String,
    @SerialName("minimap_card_outline") val minimapCardOutline: String,
    @SerialName("minimap_frame_outline") val minimapFrameOutline: String,
    @SerialName("minimap_viewport") val minimapViewport: String,
)

@Serializable
data class ThemeState(
    val theme: String,
    @SerialName("text_colors") val textColors: Map<String, String>,
    @SerialName("show_grid") val showGrid: Boolean = true,
)

val BUILTIN_THEMES: Map<String, ThemePalette> = mapOf(
    "light" to ThemePalette(
        bg = "#ffffff",
        grid = "#f0f0f0",
        cardDefault = "#fff9b1",
        cardOutline = "#444444",
        frameBg = "#f5f5f5",
        frameOutline = "#888888",
        frameCollapsedBg = "#e0e0ff",
        frameCollapsedOutline = "#aaaaaa",
        text = "#000000",
        connection = "#555555",
        connectionLabel = "#333333",
        minimapBg = "#ffffff",
        minimapCardOutline = "#888888",
        minimapFrameOutline = "#aaaaaa",
        minimapViewport = "#ff0000",
    ),
    "dark" to ThemePalette(
        bg = "#222222",
        grid = "#333333",
        cardDefault = "#444444",
        cardOutline = "#dddddd",
        frameBg = "#333333",
        frameOutline = "#aaaaaa",
        frameCollapsedBg = "#444466",
        frameCollapsedOutline = "#cccccc",
        text = "#ffffff",
        connection = "#dddddd",
        connectionLabel = "#eeeeee",
        minimapBg = "#222222",
        minimapCardOutline = "#aaaaaa",
        minimapFrameOutline = "#888888",
        minimapViewport = "#ff6666",
    ),
)

private val themeJson: Json = Json { ignoreUnknownKeys = true; encodeDefaults = true; prettyPrint = true }

fun loadThemeSettings(
    themes: Map<String, ThemePalette> = BUILTIN_THEMES,
    filename: Path = Paths.get(CONFIG_FILENAME),
): Triple<String, Map<String, String>, Boolean> {
    val defaultTextColors = themes.mapValues { it.value.text }
    var selectedTheme = themes.keys.firstOrNull() ?: "light"
    var textColors = defaultTextColors
    var showGrid = true

    if (Files.exists(filename)) {
        runCatching {
            Files.newInputStream(filename).use { stream ->
                val state = themeJson.decodeFromStream<ThemeState>(stream)
                if (themes.containsKey(state.theme)) selectedTheme = state.theme
                textColors = defaultTextColors + state.textColors
                showGrid = state.showGrid
            }
        }
    }
    return Triple(selectedTheme, textColors, showGrid)
}

fun saveThemeSettings(
    state: ThemeState,
    filename: Path = Paths.get(CONFIG_FILENAME),
) {
    runCatching {
        Files.createDirectories(filename.parent ?: Paths.get("."))
        Files.newOutputStream(filename).use { stream ->
            stream.write(themeJson.encodeToString(ThemeState.serializer(), state).toByteArray())
        }
    }
}
