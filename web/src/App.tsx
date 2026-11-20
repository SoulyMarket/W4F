import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuditLogPage } from './features/admin/AuditLogPage'
import { TerritoriesPage } from './features/admin/TerritoriesPage'
import { UsersPage } from './features/admin/UsersPage'
import { AuthProvider } from './features/auth/AuthContext'
import { LoginPage } from './features/auth/LoginPage'
import { MapPage } from './features/map/MapPage'
import { ProjectBoardPage } from './features/projects/ProjectBoardPage'
import { ProjectDetailPage } from './features/projects/ProjectDetailPage'
import { ReportDetailPage } from './features/reports/ReportDetailPage'
import { ReportsListPage } from './features/reports/ReportsListPage'
import { ScoringWeightsPage } from './features/scoring/ScoringWeightsPage'
import { AppLayout } from './layout/AppLayout'
import { ProtectedRoute } from './routes/ProtectedRoute'
import { RequireAdmin } from './routes/RequireAdmin'
import { RequireManager } from './routes/RequireManager'
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
                  <Route path="/projects" element={<ProjectBoardPage />} />
                  <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
                </Route>
                <Route element={<RequireAdmin />}>
                  <Route path="/admin/users" element={<UsersPage />} />
                  <Route path="/admin/audit" element={<AuditLogPage />} />
                  <Route path="/admin/territories" element={<TerritoriesPage />} />
                </Route>
                <Route element={<RequireManager />}>
                  <Route path="/map" element={<MapPage />} />
                  <Route path="/scoring" element={<ScoringWeightsPage />} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
