package com.w4f.app.data.location

import android.Manifest.permission.ACCESS_FINE_LOCATION
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlin.coroutines.resume
import kotlinx.coroutines.suspendCancellableCoroutine

data class CapturedLocation(val lat: Double, val lon: Double, val accuracyM: Float)

/** Section 8, "الإثباتات": GPS is auto-captured but must never block data
 * entry — every path here returns `null` instead of throwing (missing
 * permission, no fix, provider error), and the caller treats a null
 * location exactly like a field the moqaddem can fill in later. */
interface LocationClient {
  suspend fun getCurrentLocation(): CapturedLocation?
}

class DefaultLocationClient @Inject constructor(@ApplicationContext private val context: Context) :
  LocationClient {

  private val fusedClient by lazy { LocationServices.getFusedLocationProviderClient(context) }

  override suspend fun getCurrentLocation(): CapturedLocation? {
    if (
      ContextCompat.checkSelfPermission(context, ACCESS_FINE_LOCATION) !=
        PackageManager.PERMISSION_GRANTED
    ) {
      return null
    }

    return suspendCancellableCoroutine { continuation ->
      runCatching {
          fusedClient
            .getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, null)
            .addOnSuccessListener { location ->
              val result = location?.let { CapturedLocation(it.latitude, it.longitude, it.accuracy) }
              if (continuation.isActive) continuation.resume(result)
            }
            .addOnFailureListener { if (continuation.isActive) continuation.resume(null) }
        }
        .onFailure { if (continuation.isActive) continuation.resume(null) }
    }
  }
}
