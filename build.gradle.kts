buildscript {
    repositories {
        gradlePluginPortal()
        mavenCentral()
        maven("https://cache-redirector.jetbrains.com/maven-central")
    }
    dependencies {
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.25")
        classpath("org.jetbrains.kotlin:kotlin-serialization:1.9.25")
    }
}

subprojects {
    repositories {
        mavenCentral()
        maven("https://cache-redirector.jetbrains.com/maven-central")
    }
}
