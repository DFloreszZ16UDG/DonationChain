import AccountBalanceWalletOutlined from '@mui/icons-material/AccountBalanceWalletOutlined'
import ArrowForward from '@mui/icons-material/ArrowForward'
import PaymentsOutlined from '@mui/icons-material/PaymentsOutlined'
import { Alert, Box, Button, Card, CardContent, CircularProgress, Container, Grid, LinearProgress, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, money } from '../api'
import type { Donation, DonationTrace } from '../types'

export default function MyDonationsPage() {
  const [traces, setTraces] = useState<DonationTrace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api<Donation[]>('/me/donations')
      .then((donations) => Promise.all(donations.map((item) => api<DonationTrace>(`/donations/${item.id}/trace`))))
      .then(setTraces)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Container maxWidth="lg" sx={{ py: 7 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Trazabilidad personal</Typography>
      <Typography variant="h2" sx={{ fontSize: { xs: '2.3rem', md: '3.3rem' } }}>¿Qué pasó con mi dinero?</Typography>
      <Typography color="text.secondary" sx={{ mb: 4 }}>Cada tarjeta muestra cuánto de tu aportación ya fue relacionado con gastos aprobados.</Typography>
      {loading ? <Box sx={{ display: 'grid', placeItems: 'center', py: 8 }}><CircularProgress /></Box> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}
      {!loading && !error && traces.length === 0 ? <Alert severity="info">Todavía no has registrado donaciones con esta cuenta.</Alert> : null}
      <Stack spacing={3}>
        {traces.map((trace) => {
          const percent = Number(trace.donation.amount) > 0 ? Number(trace.allocated) / Number(trace.donation.amount) * 100 : 0
          return <Card key={trace.donation.id}><CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
              <Box><Stack direction="row" spacing={1} alignItems="center"><AccountBalanceWalletOutlined color="primary" /><Typography variant="h5" fontWeight={850}>{trace.campaign_name}</Typography></Stack><Typography variant="caption" color="text.secondary">Donación {trace.donation.id} · {new Date(trace.donation.created_at).toLocaleString('es-MX')}</Typography></Box>
              <Typography variant="h4" fontWeight={850}>{money(trace.donation.amount)}</Typography>
            </Stack>
            <LinearProgress variant="determinate" value={Math.min(100, percent)} sx={{ height: 9, borderRadius: 8, mt: 3, mb: 1 }} />
            <Grid container spacing={2} sx={{ mb: 3 }}><Grid size={6}><Typography variant="caption">Asignado a gastos</Typography><Typography fontWeight={800} color="primary">{money(trace.allocated)}</Typography></Grid><Grid size={6}><Typography variant="caption">Aún disponible</Typography><Typography fontWeight={800}>{money(trace.unallocated)}</Typography></Grid></Grid>
            {trace.allocations.length ? <Stack spacing={1.2}>{trace.allocations.map((allocation) => <Box key={allocation.allocation_id} sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', p: 2, borderRadius: 2, backgroundColor: '#f4f7f3' }}><Box><Stack direction="row" spacing={1} alignItems="center"><PaymentsOutlined fontSize="small" color="secondary" /><Typography fontWeight={800}>{allocation.concept}</Typography></Stack><Typography variant="body2" color="text.secondary">{allocation.description}</Typography></Box><Typography fontWeight={850}>{money(allocation.amount)}</Typography></Box>)}</Stack> : <Alert severity="info">Esta aportación aún no ha sido utilizada en un gasto aprobado.</Alert>}
            <Button component={Link} to={`/campaigns/${trace.donation.campaign_id}`} endIcon={<ArrowForward />} sx={{ mt: 2 }}>Ver campaña completa</Button>
          </CardContent></Card>
        })}
      </Stack>
    </Container>
  )
}
