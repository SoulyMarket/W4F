import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './features/auth/AuthContext'
import { LoginPage } from './features/auth/LoginPage'
import { ReportDetailPage } from './features/reports/ReportDetailPage'
import { ReportsListPage } from './features/reports/ReportsListPage'
import { AppLayout } from './layout/AppLayout'
import { ProtectedRoute } from './routes/ProtectedRoute'
import { RequireNonMoqaddem } from './routes/RequireNonMoqaddem'
import { RoleHome } from './routes/RoleHome'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<RoleHome />} />
                <Route element={<RequireNonMoqaddem />}>
                  <Route path="/reports" element={<ReportsListPage />} />
                  <Route path="/reports/:reportId" element={<ReportDetailPage />} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
