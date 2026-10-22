import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from './api'
import type { User } from './types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (fullName: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('donationchain_token')) {
      setLoading(false)
      return
    }
    api<User>('/auth/me')
      .then(setUser)
      .catch(() => localStorage.removeItem('donationchain_token'))
      .finally(() => setLoading(false))
  }, [])

  async function authenticate(path: string, body: object) {
    const result = await api<{ access_token: string; user: User }>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    })
    localStorage.setItem('donationchain_token', result.access_token)
    setUser(result.user)
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: (email, password) => authenticate('/auth/login', { email, password }),
      register: (full_name, email, password) =>
        authenticate('/auth/register', { full_name, email, password }),
      logout: () => {
        localStorage.removeItem('donationchain_token')
        setUser(null)
      },
    }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth debe estar dentro de AuthProvider')
  return context
}
