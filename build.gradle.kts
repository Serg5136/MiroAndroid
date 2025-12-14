import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.jlleitschuh.gradle.ktlint.reporter.ReporterType

buildscript {
    repositories {
        gradlePluginPortal()
        mavenCentral()
        maven("https://cache-redirector.jetbrains.com/maven-central")
        google()
    }
    dependencies {
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.25")
        classpath("org.jetbrains.kotlin:kotlin-serialization:1.9.25")
        classpath("com.android.tools.build:gradle:8.4.2")
        classpath("com.google.gms:google-services:4.4.2")
        classpath("com.google.firebase:firebase-crashlytics-gradle:3.0.2")
    }
}

subprojects {
    repositories {
        mavenCentral()
        maven("https://cache-redirector.jetbrains.com/maven-central")
        google()
    }

    buildscript {
        repositories {
            mavenCentral()
            google()
            gradlePluginPortal()
        }
        dependencies {
            classpath("org.jlleitschuh.gradle:ktlint-gradle:11.6.1")
            classpath("io.gitlab.arturbosch.detekt:detekt-gradle-plugin:1.23.6")
        }
    }

    apply(plugin = "org.jlleitschuh.gradle.ktlint")
    apply(plugin = "io.gitlab.arturbosch.detekt")

    configure<org.jlleitschuh.gradle.ktlint.KtlintExtension> {
        val isAndroid = plugins.hasPlugin("com.android.application") || plugins.hasPlugin("com.android.library")
        android.set(isAndroid)
        outputToConsole.set(true)
        ignoreFailures.set(false)
        reporters {
            reporter(ReporterType.PLAIN)
            reporter(ReporterType.CHECKSTYLE)
        }
    }

    configure<DetektExtension> {
        buildUponDefaultConfig = true
        config.from(rootProject.file("config/detekt/detekt.yml"))
        autoCorrect = false
        source.setFrom(files("src/main/java", "src/main/kotlin", "src/test/java", "src/test/kotlin"))
        parallel = true
        ignoredBuildTypes = listOf("release")
    }

    dependencies {
        add("detektPlugins", "io.gitlab.arturbosch.detekt:detekt-formatting:1.23.6")
    }

    tasks.withType<io.gitlab.arturbosch.detekt.Detekt>().configureEach {
        reports {
            xml.required.set(true)
            html.required.set(true)
            txt.required.set(false)
            sarif.required.set(false)
        }
    }
}
