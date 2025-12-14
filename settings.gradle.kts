pluginManagement {
    repositories {
        gradlePluginPortal()
        maven("https://plugins.gradle.org/m2/")
        mavenCentral()
        google()
    }
}

rootProject.name = "MiroAndroid"
include(":core")
include(":data")
include(":app")
