import CheckCircleOutline from '@mui/icons-material/CheckCircleOutline'
import HighlightOffOutlined from '@mui/icons-material/HighlightOffOutlined'
import { Alert, Button, Card, CardContent, Chip, Container, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, money } from '../api'
import type { Expense } from '../types'

export default function ApprovalsPage() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [rejecting, setRejecting] = useState<Expense | null>(null)
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState('')

  const load = () => api<Expense[]>('/expenses/pending').then(setExpenses).catch((error: Error) => setMessage(error.message))
  useEffect(() => { void load() }, [])

  async function review(expense: Expense, approved: boolean, rejectionReason?: string) {
    try {
      await api(`/expenses/${expense.id}/review`, { method: 'POST', body: JSON.stringify({ approved, reason: rejectionReason ?? null }) })
      setMessage(approved ? 'Gasto aprobado. Ya forma parte del total utilizado.' : 'Gasto rechazado con justificación.')
      setRejecting(null); setReason(''); load()
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No fue posible revisar') }
  }

  async function autoAllocate(id: string) {
    try { await api(`/expenses/${id}/auto-allocate`, { method: 'POST' }); setMessage('El gasto quedó relacionado con donaciones disponibles.') }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No fue posible asignar') }
  }

  return (
    <Container maxWidth="md" sx={{ py: 7 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Control independiente</Typography>
      <Typography variant="h2" sx={{ fontSize: { xs: '2.3rem', md: '3.3rem' } }}>Aprobación de gastos</Typography>
      <Typography color="text.secondary" sx={{ mb: 4 }}>Revisa la descripción y el comprobante antes de afectar el saldo público.</Typography>
      {message ? <Alert severity={message.includes('aprobado') || message.includes('relacionado') ? 'success' : 'info'} sx={{ mb: 2 }}>{message}</Alert> : null}
      {expenses.length === 0 ? <Alert severity="info">No hay gastos pendientes.</Alert> : null}
      <Stack spacing={2}>
        {expenses.map((expense) => <Card key={expense.id}><CardContent sx={{ p: 3 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2}>
            <div><Chip label="Pendiente" color="warning" size="small" /><Typography variant="h5" fontWeight={800} sx={{ mt: 1 }}>{expense.concept}</Typography><Typography color="text.secondary">{expense.description}</Typography><Typography variant="caption">Comprobante: {expense.receipt_id}</Typography></div>
            <Stack alignItems={{ sm: 'flex-end' }} spacing={1}><Typography variant="h5" fontWeight={850}>{money(expense.amount)}</Typography><Stack direction="row" spacing={1}><Button color="error" startIcon={<HighlightOffOutlined />} onClick={() => setRejecting(expense)}>Rechazar</Button><Button variant="contained" startIcon={<CheckCircleOutline />} onClick={() => review(expense, true)}>Aprobar</Button></Stack></Stack>
          </Stack>
        </CardContent></Card>)}
      </Stack>
      <Dialog open={Boolean(rejecting)} onClose={() => setRejecting(null)} fullWidth>
        <DialogTitle>Justificación del rechazo</DialogTitle><DialogContent><TextField autoFocus fullWidth multiline minRows={3} label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} sx={{ mt: 1 }} /></DialogContent><DialogActions><Button onClick={() => setRejecting(null)}>Cancelar</Button><Button color="error" disabled={!reason.trim()} onClick={() => rejecting && review(rejecting, false, reason)}>Confirmar rechazo</Button></DialogActions>
      </Dialog>
    </Container>
  )
}
