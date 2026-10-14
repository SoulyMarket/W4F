package com.w4f.app.data.media

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import java.io.File
import java.io.FileOutputStream
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class MediaCompressorTest {

  private fun writeTestJpeg(width: Int, height: Int): File {
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
    val file = File.createTempFile("w4f_test", ".jpg")
    FileOutputStream(file).use { bitmap.compress(Bitmap.CompressFormat.JPEG, 100, it) }
    return file
  }

  @Test
  fun `a photo larger than the max long side is scaled down`() {
    val source = writeTestJpeg(width = 4000, height = 3000)

    val compressed = MediaCompressor.compressJpegFile(source)

    val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(compressed, 0, compressed.size, options)

    assertTrue(maxOf(options.outWidth, options.outHeight) <= MediaCompressor.MAX_LONG_SIDE_PX)
  }

  @Test
  fun `a photo already within the size limit keeps its aspect ratio`() {
    val source = writeTestJpeg(width = 800, height = 600)

    val compressed = MediaCompressor.compressJpegFile(source)

    val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(compressed, 0, compressed.size, options)

    assertTrue(options.outWidth.toDouble() / options.outHeight <= 800.0 / 600 + 0.05)
    assertTrue(options.outWidth.toDouble() / options.outHeight >= 800.0 / 600 - 0.05)
  }
}
