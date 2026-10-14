package com.w4f.app.data.media

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import androidx.exifinterface.media.ExifInterface
import java.io.ByteArrayOutputStream
import java.io.File

/** Section 8's offline-first rules: "Compress photos (max 1600 px long
 * side, JPEG ~80%)" — every photo CameraX saves goes through this before
 * it's kept, so the outbox never has to upload full-resolution originals
 * over a moqaddem's often-limited mobile data. */
object MediaCompressor {
  const val MAX_LONG_SIDE_PX = 1600
  const val JPEG_QUALITY = 80

  fun compressJpegFile(source: File): ByteArray {
    val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeFile(source.path, options)
    val sampleSize = sampleSizeFor(options.outWidth, options.outHeight, MAX_LONG_SIDE_PX)

    val decoded =
      BitmapFactory.decodeFile(source.path, BitmapFactory.Options().apply { inSampleSize = sampleSize })
        ?: error("Could not decode captured photo at ${source.path}")

    val rotated = applyExifRotation(decoded, source)
    val scaled = scaleToLongSide(rotated, MAX_LONG_SIDE_PX)

    return ByteArrayOutputStream()
      .apply { scaled.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, this) }
      .toByteArray()
  }

  private fun sampleSizeFor(width: Int, height: Int, maxLongSide: Int): Int {
    var sample = 1
    var longSide = maxOf(width, height)
    while (longSide / (sample * 2) >= maxLongSide) sample *= 2
    return sample
  }

  private fun scaleToLongSide(bitmap: Bitmap, maxLongSide: Int): Bitmap {
    val longSide = maxOf(bitmap.width, bitmap.height)
    if (longSide <= maxLongSide) return bitmap
    val scale = maxLongSide.toFloat() / longSide
    val targetWidth = (bitmap.width * scale).toInt().coerceAtLeast(1)
    val targetHeight = (bitmap.height * scale).toInt().coerceAtLeast(1)
    return Bitmap.createScaledBitmap(bitmap, targetWidth, targetHeight, true)
  }

  private fun applyExifRotation(bitmap: Bitmap, source: File): Bitmap {
    val degrees =
      runCatching {
          when (ExifInterface(source.path).getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL,
          )) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> 0f
          }
        }
        .getOrDefault(0f)
    if (degrees == 0f) return bitmap
    val matrix = Matrix().apply { postRotate(degrees) }
    return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
  }
}
