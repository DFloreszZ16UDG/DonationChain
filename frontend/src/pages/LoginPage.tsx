import LockOutlined from '@mui/icons-material/LockOutlined'
import { Alert, Box, Button, Card, CardContent, Chip, Container, Divider, Stack, Tab, Tabs, TextField, Typography } from '@mui/material'
import { FormEvent, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const demos = [
  ['Donante', 'donante@donationchain.example.com'],
  ['Organización', 'organizacion@donationchain.example.com'],
  ['Auditor', 'auditor@donationchain.example.com'],
  ['Administrador', 'admin@donationchain.example.com'],
]

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('donante@donationchain.example.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [working, setWorking] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setWorking(true)
    try {
      if (mode === 'login') await login(email, password)
      else await register(name, email, password)
      const from = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(from, { replace: true })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No fue posible ingresar')
    } finally {
      setWorking(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card><CardContent sx={{ p: { xs: 3, sm: 5 } }}>
        <Box className="login-icon"><LockOutlined /></Box>
        <Typography variant="h4" fontWeight={850} textAlign="center">Acceso seguro</Typography>
        <Typography color="text.secondary" textAlign="center" sx={{ mt: 1, mb: 3 }}>Consulta o registra información según tu rol.</Typography>
        <Tabs value={mode} onChange={(_, value) => setMode(value)} variant="fullWidth" sx={{ mb: 3 }}>
          <Tab value="login" label="Ingresar" />
          <Tab value="register" label="Crear cuenta de donante" />
        </Tabs>
        <Box component="form" onSubmit={submit}>
          <Stack spacing={2.2}>
            {mode === 'register' ? <TextField label="Nombre completo" value={name} onChange={(e) => setName(e.target.value)} required /> : null}
            <TextField type="email" label="Correo electrónico" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <TextField type="password" label="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} required inputProps={{ minLength: 10 }} />
            {error ? <Alert severity="error">{error}</Alert> : null}
            <Button type="submit" variant="contained" size="large" disabled={working}>{working ? 'Verificando…' : mode === 'login' ? 'Ingresar' : 'Crear cuenta'}</Button>
          </Stack>
        </Box>
        {mode === 'login' ? (
          <><Divider sx={{ my: 3 }}>cuentas del piloto local</Divider>
          <Stack direction="row" flexWrap="wrap" gap={1}>
            {demos.map(([label, demoEmail]) => <Chip key={demoEmail} label={label} onClick={() => setEmail(demoEmail)} />)}
          </Stack>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1.5 }}>Usa la contraseña local definida como DEMO_PASSWORD en el backend. Nunca reutilices esa contraseña en producción.</Typography></>
        ) : null}
      </CardContent></Card>
    </Container>
  )
}
