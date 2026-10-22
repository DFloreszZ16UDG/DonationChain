import ArrowForward from '@mui/icons-material/ArrowForward'
import BoltOutlined from '@mui/icons-material/BoltOutlined'
import ReceiptLongOutlined from '@mui/icons-material/ReceiptLongOutlined'
import VerifiedUserOutlined from '@mui/icons-material/VerifiedUserOutlined'
import { Alert, Box, Button, Card, CardActions, CardContent, Chip, CircularProgress, Container, Grid, LinearProgress, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, money } from '../api'
import type { BlockchainStatus, Campaign } from '../types'

export default function HomePage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [chain, setChain] = useState<BlockchainStatus | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api<Campaign[]>('/campaigns'), api<BlockchainStatus>('/blockchain/status')])
      .then(([items, status]) => { setCampaigns(items); setChain(status) })
      .catch((reason: Error) => setError(reason.message))
  }, [])

  return (
    <>
      <Box className="hero">
        <Container maxWidth="lg">
          <Grid container spacing={5} alignItems="center">
            <Grid size={{ xs: 12, md: 7 }}>
              <Chip label="Del donativo al resultado" color="secondary" sx={{ mb: 2, fontWeight: 800 }} />
              <Typography variant="h1" sx={{ fontSize: { xs: '2.7rem', md: '4.7rem' }, maxWidth: 800 }}>
                Mira con claridad qué pasó con tu dinero.
              </Typography>
              <Typography sx={{ mt: 2.5, fontSize: '1.2rem', color: 'rgba(255,255,255,.78)', maxWidth: 680 }}>
                Cada donación, gasto, comprobante y aprobación deja una evidencia consultable y una huella imposible de cambiar sin ser detectada.
              </Typography>
              <Button component="a" href="#campanias" variant="contained" color="secondary" size="large" endIcon={<ArrowForward />} sx={{ mt: 4 }}>Explorar campañas</Button>
            </Grid>
            <Grid size={{ xs: 12, md: 5 }}>
              <Box className="trust-card">
                <Typography variant="overline">Estado de la red</Typography>
                <Typography variant="h5" sx={{ mt: 1 }}>{chain?.network ?? 'Consultando Sepolia…'}</Typography>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mt: 2 }}>
                  <Box className={chain?.rpc_connected ? 'status-dot online' : 'status-dot'} />
                  <Typography>{chain?.message ?? 'Verificando conexión'}</Typography>
                </Stack>
                {chain?.latest_block ? <Typography variant="body2" sx={{ opacity: .72, mt: 1 }}>Bloque más reciente: {chain.latest_block.toLocaleString()}</Typography> : null}
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ mt: -4, position: 'relative' }}>
        <Grid container spacing={2}>
          {[
            [<ReceiptLongOutlined />, 'Comprobantes reales', 'PDF e imágenes protegidos mediante SHA-256.'],
            [<VerifiedUserOutlined />, 'Gastos aprobados', 'Un auditor revisa antes de afectar el saldo.'],
            [<BoltOutlined />, 'Rastro verificable', 'Auditoría encadenada y preparada para Blockchain.'],
          ].map(([icon, title, text]) => (
            <Grid size={{ xs: 12, md: 4 }} key={String(title)}>
              <Card sx={{ height: '100%' }}><CardContent><Box color="primary.main">{icon}</Box><Typography variant="h6" fontWeight={800} sx={{ my: 1 }}>{title}</Typography><Typography color="text.secondary">{text}</Typography></CardContent></Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Container id="campanias" maxWidth="lg" sx={{ py: 9 }}>
        <Typography variant="overline" color="primary" fontWeight={800}>Campañas</Typography>
        <Typography variant="h2" sx={{ fontSize: { xs: '2rem', md: '3rem' }, mb: 1 }}>Transparencia desde el primer peso</Typography>
        <Typography color="text.secondary" sx={{ mb: 4 }}>Consulta el total recibido, utilizado y disponible de cada iniciativa.</Typography>
        {error ? <Alert severity="error">{error}. Comprueba que la API esté encendida.</Alert> : null}
        {!error && campaigns.length === 0 ? <CircularProgress /> : null}
        <Grid container spacing={3}>
          {campaigns.map((campaign) => {
            const progress = Math.min(100, Number(campaign.donated) / Number(campaign.goal_amount) * 100)
            return (
              <Grid size={{ xs: 12, md: 6 }} key={campaign.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flex: 1, p: 3 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                      <Chip label={campaign.status === 'ACTIVE' ? 'Activa' : campaign.status} color={campaign.status === 'ACTIVE' ? 'success' : 'default'} size="small" />
                      <Typography variant="caption" color="text.secondary">Meta {money(campaign.goal_amount)}</Typography>
                    </Stack>
                    <Typography variant="h5" fontWeight={800}>{campaign.name}</Typography>
                    <Typography color="text.secondary" sx={{ my: 2 }}>{campaign.description}</Typography>
                    <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 8, mb: 2 }} />
                    <Grid container spacing={2}>
                      <Grid size={4}><Typography variant="caption">Recaudado</Typography><Typography fontWeight={800}>{money(campaign.donated)}</Typography></Grid>
                      <Grid size={4}><Typography variant="caption">Utilizado</Typography><Typography fontWeight={800}>{money(campaign.spent)}</Typography></Grid>
                      <Grid size={4}><Typography variant="caption">Disponible</Typography><Typography fontWeight={800} color="primary">{money(campaign.available)}</Typography></Grid>
                    </Grid>
                  </CardContent>
                  <CardActions sx={{ px: 3, pb: 3 }}><Button component={Link} to={`/campaigns/${campaign.id}`} endIcon={<ArrowForward />}>Ver trazabilidad</Button></CardActions>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      </Container>
    </>
  )
}
