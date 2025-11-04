import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export const useBoardWebSocket = (boardId: string, token: string) => {
  const queryClient = useQueryClient()
  useEffect(() => {
    if (!boardId || !token) return
    const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/api/v1/ws/board/${boardId}?token=${token}`)
    ws.onmessage = () => queryClient.invalidateQueries({ queryKey: ['board', boardId] })
    return () => ws.close()
  }, [boardId, token, queryClient])
}
