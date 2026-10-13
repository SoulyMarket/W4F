package com.w4f.app.i18n

import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import org.junit.Assert.assertTrue
import org.junit.Test
import org.w3c.dom.Element

/**
 * Mirrors the backend's i18n key-parity test (section 2.1: "Never hard-code
 * UI text: every string lives in resource/translation files with both `ar`
 * and `fr` versions from day one"). Pure JVM/file-system test — no Android
 * runtime needed, so it always runs regardless of emulator availability.
 */
class StringResourceParityTest {

    private fun stringKeys(path: String): Set<String> {
        val file = File(path)
        assertTrue("missing string resource file: $path", file.exists())
        val doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(file)
        val nodes = doc.getElementsByTagName("string")
        return (0 until nodes.length)
            .map { (nodes.item(it) as Element).getAttribute("name") }
            .toSet()
    }

    @Test
    fun `arabic default and french string resources have identical key sets`() {
        val arabicKeys = stringKeys("src/main/res/values/strings.xml")
        val frenchKeys = stringKeys("src/main/res/values-fr/strings.xml")

        val missingInFrench = arabicKeys - frenchKeys
        val missingInArabic = frenchKeys - arabicKeys

        assertTrue("keys missing in values-fr/strings.xml: $missingInFrench", missingInFrench.isEmpty())
        assertTrue("keys missing in values/strings.xml: $missingInArabic", missingInArabic.isEmpty())
    }
}
