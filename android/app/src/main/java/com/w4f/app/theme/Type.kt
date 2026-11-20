package com.w4f.app.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.w4f.app.R

// Noto Sans Arabic renders Arabic, Latin, and digits from the same bundled
// font — see res/font/noto_sans_arabic.xml for why this is bundled rather
// than a downloadable Google Fonts reference.
val NotoSansArabicFamily =
  FontFamily(
    Font(R.font.noto_sans_arabic_regular, FontWeight.Normal),
    Font(R.font.noto_sans_arabic_bold, FontWeight.Bold),
  )

// A distinct heading/display face — the same "real heading hierarchy
// instead of one weight doing double duty" change made to the web
// dashboard's own `font-heading` token (Lexend/Noto Kufi Arabic pairing
// from the ui-ux-pro-max pass), scoped here to titleLarge/titleMedium
// only (actual screen/section titles) — not labelLarge, which M3 also
// uses for button text, where a display face would look misapplied.
val NotoKufiArabicFamily = FontFamily(Font(R.font.noto_kufi_arabic, FontWeight.Normal))

val Typography =
  Typography(
    bodyLarge =
      TextStyle(
        fontFamily = NotoSansArabicFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp,
      ),
    bodyMedium =
      TextStyle(
        fontFamily = NotoSansArabicFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp,
      ),
    titleLarge =
      TextStyle(
        fontFamily = NotoKufiArabicFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 22.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp,
      ),
    titleMedium =
      TextStyle(
        fontFamily = NotoKufiArabicFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 18.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.sp,
      ),
    labelLarge =
      TextStyle(
        fontFamily = NotoSansArabicFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 16.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp,
      ),
  )
