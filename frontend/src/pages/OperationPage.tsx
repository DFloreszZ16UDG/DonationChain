import CloudUploadOutlined from '@mui/icons-material/CloudUploadOutlined'
import { Alert, Button, Card, CardContent, Container, Stack, TextField, Typography } from '@mui/material'
import { FormEvent, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

export default function OperationPage({ kind }: { kind: 'donation' | 'expense' }) {
  const { campaignId = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [amount, setAmount] = useState('')
  const [name, setName] = useState(user?.full_name ?? '')
  const [concept, setConcept] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [working, setWorking] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (kind === 'expense' && !file) { setError('El comprobante es obligatorio para solicitar un gasto.'); return }
    const data = new FormData()
    data.append('amount', amount)
    if (kind === 'donation') data.append('donor_name', name)
    else { data.append('concept', concept); data.append('description', description) }
    if (file) data.append('receipt_file', file)
    setWorking(true)
    try {
      const endpoint = kind === 'donation' ? 'donations' : 'expenses'
      await api(`/campaigns/${campaignId}/${endpoint}`, { method: 'POST', body: data })
      navigate(`/campaigns/${campaignId}`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No fue posible guardar la operación')
    } finally { setWorking(false) }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 7 }}>
      <Card><CardContent sx={{ p: { xs: 3, sm: 5 } }}>
        <Typography variant="overline" color="primary" fontWeight={800}>{kind === 'donation' ? 'Nueva aportación' : 'Uso de recursos'}</Typography>
        <Typography variant="h3" sx={{ mb: 1 }}>{kind === 'donation' ? 'Registrar donación' : 'Solicitar aprobación de gasto'}</Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>{kind === 'donation' ? 'El monto se suma al saldo de la campaña. El comprobante es opcional.' : 'El gasto no reducirá el saldo hasta que un auditor lo apruebe.'}</Typography>
        <Stack component="form" spacing={2.2} onSubmit={submit}>
          {kind === 'donation' ? <TextField label="Nombre visible del donante" value={name} onChange={(e) => setName(e.target.value)} required inputProps={{ minLength: 2 }} /> : (
            <>
              <TextField label="Concepto" value={concept} onChange={(e) => setConcept(e.target.value)} required />
              <TextField label="Descripción del uso" value={description} onChange={(e) => setDescription(e.target.value)} required multiline minRows={3} />
            </>
          )}
          <TextField label="Monto en MXN" value={amount} onChange={(e) => setAmount(e.target.value)} required type="number" inputProps={{ min: '0.01', step: '0.01' }} helperText="Se aceptan como máximo dos decimales." />
          <Button component="label" variant="outlined" startIcon={<CloudUploadOutlined />}>
            {file ? file.name : kind === 'expense' ? 'Seleccionar comprobante obligatorio' : 'Agregar comprobante opcional'}
            <input hidden type="file" accept="application/pdf,image/png,image/jpeg" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Button>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Button type="submit" variant="contained" size="large" disabled={working}>{working ? 'Guardando…' : kind === 'donation' ? 'Registrar donación' : 'Enviar a aprobación'}</Button>
        </Stack>
      </CardContent></Card>
    </Container>
  )
}
