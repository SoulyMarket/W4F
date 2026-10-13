package com.w4f.app

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import com.w4f.app.ui.home.HomeScreen
import com.w4f.app.ui.login.LoginScreen

@Composable
fun MainNavigation(rootViewModel: RootViewModel = hiltViewModel()) {
  val hasSession by rootViewModel.hasSession.collectAsState()
  val backStack = rememberNavBackStack(if (hasSession) Home else Login)

  NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    entryProvider =
      entryProvider {
        entry<Login> {
          LoginScreen(
            onLoginSuccess = {
              backStack.clear()
              backStack.add(Home)
            },
            modifier = Modifier.safeDrawingPadding().padding(16.dp),
          )
        }
        entry<Home> {
          HomeScreen(
            onLoggedOut = {
              backStack.clear()
              backStack.add(Login)
            },
            modifier = Modifier.safeDrawingPadding().padding(16.dp),
          )
        }
      },
  )
}
