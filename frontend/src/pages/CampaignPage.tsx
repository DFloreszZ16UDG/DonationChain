import AddCardOutlined from '@mui/icons-material/AddCardOutlined'
import ArrowBack from '@mui/icons-material/ArrowBack'
import AttachFileOutlined from '@mui/icons-material/AttachFileOutlined'
import PaymentsOutlined from '@mui/icons-material/PaymentsOutlined'
import VerifiedOutlined from '@mui/icons-material/VerifiedOutlined'
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Container, Dialog, DialogActions, DialogContent, DialogTitle, Grid, LinearProgress, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, money, shortHash } from '../api'
import { useAuth } from '../auth'
import type { Campaign, TimelineEvent } from '../types'

export default function CampaignPage() {
  const { campaignId = '' } = useParams()
  const { user } = useAuth()
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [verify, setVerify] = useState<TimelineEvent | null>(null)
  const [result, setResult] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api<Campaign>(`/campaigns/${campaignId}`),
      api<TimelineEvent[]>(`/campaigns/${campaignId}/timeline`),
    ]).then(([item, events]) => { setCampaign(item); setTimeline(events) }).catch((reason: Error) => setError(reason.message))
  }, [campaignId])

  async function verifyFile(file: File) {
    if (!verify?.receipt_id) return
    const data = new FormData()
    data.append('receipt_file', file)
    try {
      const response = await api<{ matches: boolean; uploaded_sha256: string }>(`/receipts/${verify.receipt_id}/verify`, { method: 'POST', body: data })
      setResult(response.matches ? 'Coincide: el archivo conserva exactamente la huella registrada.' : 'No coincide: el archivo fue modificado o no es el comprobante original.')
    } catch (reason) {
      setResult(reason instanceof Error ? reason.message : 'No fue posible verificar')
    }
  }

  if (error) return <Container sx={{ py: 8 }}><Alert severity="error">{error}</Alert></Container>
  if (!campaign) return <Box sx={{ display: 'grid', minHeight: '70vh', placeItems: 'center' }}><CircularProgress /></Box>
  const progress = Math.min(100, Number(campaign.donated) / Number(campaign.goal_amount) * 100)

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Button component={Link} to="/" startIcon={<ArrowBack />} sx={{ mb: 2 }}>Todas las campañas</Button>
      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Chip label={campaign.status === 'ACTIVE' ? 'Campaña activa' : campaign.status} color="success" />
          <Typography variant="h2" sx={{ mt: 2, fontSize: { xs: '2.3rem', md: '3.6rem' } }}>{campaign.name}</Typography>
          <Typography color="text.secondary" fontSize="1.1rem" sx={{ mt: 2 }}>{campaign.description}</Typography>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card><CardContent sx={{ p: 3 }}>
            <Typography variant="overline">Progreso</Typography>
            <Typography variant="h4" fontWeight={850}>{money(campaign.donated)}</Typography>
            <Typography color="text.secondary">de {money(campaign.goal_amount)}</Typography>
            <LinearProgress variant="determinate" value={progress} sx={{ height: 9, borderRadius: 5, my: 2 }} />
            <Stack direction="row" justifyContent="space-between"><Typography>Utilizado</Typography><Typography fontWeight={800}>{money(campaign.spent)}</Typography></Stack>
            <Stack direction="row" justifyContent="space-between"><Typography>Disponible</Typography><Typography fontWeight={800} color="primary">{money(campaign.available)}</Typography></Stack>
            <Button component={Link} to={`/campaigns/${campaign.id}/donate`} variant="contained" fullWidth sx={{ mt: 3 }} startIcon={<AddCardOutlined />}>Registrar donación</Button>
            {user?.role === 'ORGANIZATION' || user?.role === 'ADMIN' ? <Button component={Link} to={`/campaigns/${campaign.id}/expense`} fullWidth sx={{ mt: 1 }} startIcon={<PaymentsOutlined />}>Solicitar gasto</Button> : null}
          </CardContent></Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 7 }}>
        <Typography variant="overline" color="primary" fontWeight={800}>Historial público</Typography>
        <Typography variant="h3" sx={{ mb: 3 }}>Así se ha utilizado el dinero</Typography>
        {timeline.length === 0 ? <Alert severity="info">Aún no hay movimientos registrados en esta campaña.</Alert> : null}
        <Stack spacing={2}>
          {timeline.map((event) => (
            <Card key={event.id}><CardContent sx={{ p: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid size={{ xs: 12, sm: 7 }}>
                  <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                    {event.event_type === 'DONATION' ? <AddCardOutlined color="primary" /> : <PaymentsOutlined color="secondary" />}
                    <Typography variant="h6" fontWeight={800}>{event.title}</Typography>
                    <Chip size="small" label={event.status} color={event.status === 'APPROVED' || event.status === 'REGISTRADA' ? 'success' : event.status === 'REJECTED' ? 'error' : 'default'} />
                  </Stack>
                  <Typography color="text.secondary">{event.description}</Typography>
                  <Typography variant="caption" color="text.secondary">{new Date(event.created_at).toLocaleString('es-MX')}</Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 2 }}><Typography variant="h6" fontWeight={850}>{event.amount ? money(event.amount) : '—'}</Typography></Grid>
                <Grid size={{ xs: 12, sm: 3 }} textAlign={{ sm: 'right' }}>
                  {event.receipt_id ? <Button startIcon={<AttachFileOutlined />} onClick={() => { setVerify(event); setResult('') }}>Verificar comprobante</Button> : <Typography variant="caption">Sin comprobante</Typography>}
                  {event.receipt_hash ? <Typography variant="caption" display="block" title={event.receipt_hash}>SHA-256 {shortHash(event.receipt_hash)}</Typography> : null}
                </Grid>
              </Grid>
            </CardContent></Card>
          ))}
        </Stack>
      </Box>

      <Dialog open={Boolean(verify)} onClose={() => setVerify(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Verificar integridad del comprobante</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ mb: 2 }}>Selecciona el archivo original. El sistema calculará su SHA-256 y lo comparará con la huella registrada.</Typography>
          <Button component="label" variant="outlined" startIcon={<VerifiedOutlined />}>Seleccionar archivo<input hidden type="file" accept="application/pdf,image/png,image/jpeg" onChange={(e) => e.target.files?.[0] && verifyFile(e.target.files[0])} /></Button>
          {result ? <Alert severity={result.startsWith('Coincide') ? 'success' : 'warning'} sx={{ mt: 2 }}>{result}</Alert> : null}
        </DialogContent>
        <DialogActions><Button onClick={() => setVerify(null)}>Cerrar</Button></DialogActions>
      </Dialog>
    </Container>
  )
}
