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
}
