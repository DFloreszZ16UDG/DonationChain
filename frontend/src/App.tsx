import { CircularProgress, Box } from '@mui/material'
import { lazy, Suspense, type ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import type { Role } from './types'

const HomePage = lazy(() => import('./pages/HomePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const CampaignPage = lazy(() => import('./pages/CampaignPage'))
const CampaignCreatePage = lazy(() => import('./pages/CampaignCreatePage'))
const OperationPage = lazy(() => import('./pages/OperationPage'))
const ApprovalsPage = lazy(() => import('./pages/ApprovalsPage'))
const AuditPage = lazy(() => import('./pages/AuditPage'))
const MyDonationsPage = lazy(() => import('./pages/MyDonationsPage'))

function Protected({ children, roles }: { children: ReactNode; roles?: Role[] }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Box sx={{ display: 'grid', minHeight: '70vh', placeItems: 'center' }}><CircularProgress /></Box>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Suspense fallback={<Box sx={{ display: 'grid', minHeight: '70vh', placeItems: 'center' }}><CircularProgress /></Box>}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/campaigns/:campaignId" element={<CampaignPage />} />
          <Route path="/campaigns/new" element={<Protected roles={['ADMIN', 'ORGANIZATION']}><CampaignCreatePage /></Protected>} />
          <Route path="/campaigns/:campaignId/donate" element={<Protected><OperationPage kind="donation" /></Protected>} />
          <Route path="/campaigns/:campaignId/expense" element={<Protected roles={['ADMIN', 'ORGANIZATION']}><OperationPage kind="expense" /></Protected>} />
          <Route path="/approvals" element={<Protected roles={['ADMIN', 'AUDITOR']}><ApprovalsPage /></Protected>} />
          <Route path="/audit" element={<Protected roles={['ADMIN', 'AUDITOR']}><AuditPage /></Protected>} />
          <Route path="/my-donations" element={<Protected><MyDonationsPage /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
