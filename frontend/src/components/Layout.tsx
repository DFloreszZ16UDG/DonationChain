import AccountCircleOutlined from '@mui/icons-material/AccountCircleOutlined'
import AddCircleOutline from '@mui/icons-material/AddCircleOutline'
import FactCheckOutlined from '@mui/icons-material/FactCheckOutlined'
import LogoutOutlined from '@mui/icons-material/LogoutOutlined'
import ShieldOutlined from '@mui/icons-material/ShieldOutlined'
import AccountBalanceWalletOutlined from '@mui/icons-material/AccountBalanceWalletOutlined'
import { AppBar, Box, Button, Chip, Container, IconButton, Toolbar, Typography } from '@mui/material'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const roleLabels = {
  ADMIN: 'Administrador',
  ORGANIZATION: 'Organización',
  DONOR: 'Donante',
  AUDITOR: 'Auditor',
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: '1px solid #e4e9e3', backdropFilter: 'blur(16px)', backgroundColor: 'rgba(255,255,255,.9)' }}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ gap: 1.5, minHeight: 70 }}>
            <Box component={Link} to="/" sx={{ display: 'flex', gap: 1, alignItems: 'center', textDecoration: 'none', color: 'primary.dark', mr: 'auto' }}>
              <Box className="brand-mark">DC</Box>
              <Box>
                <Typography fontWeight={850} lineHeight={1}>DonationChain</Typography>
                <Typography variant="caption" color="text.secondary">Transparencia verificable</Typography>
              </Box>
            </Box>
            {user?.role === 'ORGANIZATION' || user?.role === 'ADMIN' ? (
              <>
                <Button component={Link} to="/campaigns/new" startIcon={<AddCircleOutline />} sx={{ display: { xs: 'none', md: 'inline-flex' } }}>Nueva campaña</Button>
                <IconButton component={Link} to="/campaigns/new" aria-label="Nueva campaña" color="primary" sx={{ display: { md: 'none' } }}><AddCircleOutline /></IconButton>
              </>
            ) : null}
            {user?.role === 'AUDITOR' || user?.role === 'ADMIN' ? (
              <>
                <Button component={Link} to="/approvals" startIcon={<FactCheckOutlined />} sx={{ display: { xs: 'none', md: 'inline-flex' } }}>Aprobaciones</Button>
                <Button component={Link} to="/audit" startIcon={<ShieldOutlined />} sx={{ display: { xs: 'none', md: 'inline-flex' } }}>Auditoría</Button>
                <IconButton component={Link} to="/approvals" aria-label="Aprobaciones" color="primary" sx={{ display: { md: 'none' } }}><FactCheckOutlined /></IconButton>
                <IconButton component={Link} to="/audit" aria-label="Auditoría" color="primary" sx={{ display: { md: 'none' } }}><ShieldOutlined /></IconButton>
              </>
            ) : null}
            {user?.role === 'DONOR' ? (
              <>
                <Button component={Link} to="/my-donations" startIcon={<AccountBalanceWalletOutlined />} sx={{ display: { xs: 'none', md: 'inline-flex' } }}>Mi dinero</Button>
                <IconButton component={Link} to="/my-donations" aria-label="Mi dinero" color="primary" sx={{ display: { md: 'none' } }}><AccountBalanceWalletOutlined /></IconButton>
              </>
            ) : null}
            {user ? (
              <>
                <Chip icon={<AccountCircleOutlined />} label={`${user.full_name} · ${roleLabels[user.role]}`} variant="outlined" sx={{ display: { xs: 'none', sm: 'inline-flex' } }} />
                <IconButton aria-label="Cerrar sesión" onClick={() => { logout(); navigate('/') }}><LogoutOutlined /></IconButton>
              </>
            ) : (
              <Button component={Link} to="/login" variant="contained">Ingresar</Button>
            )}
          </Toolbar>
        </Container>
      </AppBar>
      <Outlet />
      <Box component="footer" sx={{ borderTop: '1px solid #e0e6df', mt: 10, py: 4 }}>
        <Container maxWidth="lg" sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: 1 }}>
          <Typography color="text.secondary">DonationChain · Piloto académico con arquitectura real</Typography>
          <Typography color="text.secondary">Los comprobantes permanecen fuera de Blockchain; solo se ancla su hash.</Typography>
        </Container>
      </Box>
    </Box>
  )
}
