import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export const useNotificationsWebSocket = (token: string) => {
  const queryClient = useQueryClient()
  useEffect(() => {
    if (!token) return
    const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/api/v1/ws/notifications?token=${token}`)
    ws.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
    }
    return () => ws.close()
  }, [token, queryClient])
}
