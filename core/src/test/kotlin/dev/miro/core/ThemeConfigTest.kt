package dev.miro.core

import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ThemeConfigTest {
    @Test
    fun `loadThemeSettings returns defaults when file absent`() {
        val tempPath = Files.createTempDirectory("theme-test").resolve("missing.json")
        val (theme, textColors, showGrid) = loadThemeSettings(filename = tempPath)

        assertEquals("light", theme)
        assertTrue(textColors.isNotEmpty())
        assertTrue(showGrid)
    }

    @Test
    fun `save and load theme state`() {
        val dir = Files.createTempDirectory("theme-save")
        val target: Path = dir.resolve("config.json")
        val state = ThemeState(theme = "dark", textColors = mapOf("dark" to "#fff"), showGrid = false)

        saveThemeSettings(state, filename = target)
        val (theme, textColors, showGrid) = loadThemeSettings(filename = target)

        assertEquals("dark", theme)
        assertEquals("#fff", textColors["dark"])
        assertTrue(!showGrid)
    }
}
