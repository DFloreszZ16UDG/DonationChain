import { Alert, Button, Card, CardContent, Container, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

interface Organization { id: string; name: string }

export default function CampaignCreatePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [organizationId, setOrganizationId] = useState(user?.organization_id ?? '')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [goal, setGoal] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (user?.role === 'ADMIN') api<Organization[]>('/admin/organizations').then(setOrganizations).catch(() => undefined)
  }, [user])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const campaign = await api<{ id: string }>('/campaigns', {
        method: 'POST',
        body: JSON.stringify({ organization_id: organizationId || null, name, description, goal_amount: goal }),
      })
      navigate(`/campaigns/${campaign.id}`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No fue posible crear la campaña') }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 7 }}><Card><CardContent sx={{ p: { xs: 3, sm: 5 } }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Organización</Typography>
      <Typography variant="h3" sx={{ mb: 3 }}>Crear campaña</Typography>
      <Stack component="form" spacing={2.2} onSubmit={submit}>
        {user?.role === 'ADMIN' ? <TextField select label="Organización" value={organizationId} onChange={(e) => setOrganizationId(e.target.value)} required>{organizations.map((org) => <MenuItem key={org.id} value={org.id}>{org.name}</MenuItem>)}</TextField> : null}
        <TextField label="Nombre de la campaña" value={name} onChange={(e) => setName(e.target.value)} required />
        <TextField label="Descripción pública" value={description} onChange={(e) => setDescription(e.target.value)} required multiline minRows={4} inputProps={{ minLength: 10 }} />
        <TextField label="Meta en MXN" value={goal} onChange={(e) => setGoal(e.target.value)} required type="number" inputProps={{ min: '.01', step: '.01' }} />
        <Alert severity="info">La campaña se crea como borrador. Actívala desde la API administrativa antes de recibir donaciones.</Alert>
        {error ? <Alert severity="error">{error}</Alert> : null}
        <Button type="submit" variant="contained" size="large">Crear campaña</Button>
      </Stack>
    </CardContent></Card></Container>
  )
}
