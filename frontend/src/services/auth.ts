import api from '@/lib/api'
import { LoginRequest, RegisterRequest, AuthTokens, User } from '@/types'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthTokens> => {
    const response = await api.post('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<AuthTokens> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },
}
