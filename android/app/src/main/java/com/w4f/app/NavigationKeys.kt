package com.w4f.app

import androidx.navigation3.runtime.NavKey
import kotlinx.serialization.Serializable

@Serializable data object Login : NavKey

@Serializable data object Home : NavKey

@Serializable data object NewReport : NavKey

@Serializable data class DossierDetail(val reportId: String) : NavKey

@Serializable data object Notifications : NavKey

// Named MapRoute, not Map — a bare `Map` in this package would shadow
// `kotlin.collections.Map`'s implicit default import for every file here.
@Serializable data object MapRoute : NavKey
