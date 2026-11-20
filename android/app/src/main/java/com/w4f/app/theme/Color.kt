package com.w4f.app.theme

import androidx.compose.ui.graphics.Color

// W4F's brand palette — the same tokens as the web dashboard's
// `index.css` `@theme` block (sky/cyan, a "water" association fitting
// the project), so the Android app and the web dashboard read as one
// product instead of two unrelated ones. Previously this file still had
// Android Studio's unmodified "Empty Compose Activity" template colors
// (Purple80/Purple40/Pink...), and `W4FTheme` additionally defaulted to
// Material You dynamic color on Android 12+, so the app's actual on-
// screen color had nothing to do with either palette — it came from
// whatever the device's wallpaper happened to produce.

val LightPrimary = Color(0xFF0284C7)
val LightOnPrimary = Color(0xFFFFFFFF)
val LightSecondary = Color(0xFF06B6D4)
val LightOnSecondary = Color(0xFF00282E)
val LightTertiary = Color(0xFF0891B2)
val LightOnTertiary = Color(0xFFFFFFFF)
val LightBackground = Color(0xFFF0F9FF)
val LightOnBackground = Color(0xFF0F172A)
val LightSurfaceVariant = Color(0xFFEFF7FB)
val LightOnSurfaceVariant = Color(0xFF51657A)
val LightOutline = Color(0xFFBFD9E8)
val LightError = Color(0xFFDC2626)
val LightOnError = Color(0xFFFFFFFF)

val DarkPrimary = Color(0xFF38BDF8)
val DarkOnPrimary = Color(0xFF0B1220)
val DarkSecondary = Color(0xFF22D3EE)
val DarkOnSecondary = Color(0xFF00282E)
val DarkTertiary = Color(0xFF2DD4BF)
val DarkOnTertiary = Color(0xFF00201C)
val DarkBackground = Color(0xFF0B1220)
val DarkOnBackground = Color(0xFFE2E8F0)
val DarkSurfaceVariant = Color(0xFF111C2E)
val DarkOnSurfaceVariant = Color(0xFF93A4BB)
val DarkOutline = Color(0xFF32465E)
val DarkError = Color(0xFFF87171)
val DarkOnError = Color(0xFF450A0A)
