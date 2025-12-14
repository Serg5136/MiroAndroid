package com.miro.data.network

import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import okhttp3.Cache
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.create
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.io.File
import java.util.concurrent.TimeUnit
import kotlin.time.Duration
import kotlin.time.Duration.Companion.seconds
import kotlin.time.toJavaDuration
import okhttp3.MediaType.Companion.toMediaType

class NetworkModule(
    cacheDir: File,
    private val baseUrl: String,
    private val timeout: Duration = 20.seconds,
    private val interceptors: List<Interceptor> = emptyList(),
) {
    private val json = Json { ignoreUnknownKeys = true }

    private val okHttpClient: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        OkHttpClient.Builder()
            .cache(Cache(directory = cacheDir, maxSize = 10L * 1024L * 1024L))
            .connectTimeout(timeout.toJavaDuration())
            .readTimeout(timeout.toJavaDuration())
            .writeTimeout(timeout.toJavaDuration())
            .addInterceptor { chain ->
                val request = chain.request()
                    .newBuilder()
                    .header("Accept", "application/json")
                    .build()
                chain.proceed(request)
            }
            .apply { interceptors.forEach { addInterceptor(it) } }
            .addNetworkInterceptor(logging)
            .build()
    }

    @OptIn(ExperimentalSerializationApi::class)
    val api: BoardApi by lazy {
        val contentType = "application/json".toMediaType()
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create()
    }
}
