import api from '@/lib-custom/api'
import { Board, CreateBoardRequest } from '@/types'

export interface BoardMember {
  id: string
  email: string
  full_name: string
  role: string
  joined_at: string
}

export const boardsApi = {
  getBoards: async (): Promise<Board[]> => {
    const response = await api.get('/boards')
    return response.data
  },

  getBoard: async (boardId: string): Promise<Board> => {
    const response = await api.get(`/boards/${boardId}`)
    return response.data
  },

  getBoardMembers: async (boardId: string): Promise<{ members: BoardMember[] }> => {
    const response = await api.get(`/boards/${boardId}/members`)
    return response.data
  },

  createBoard: async (data: CreateBoardRequest): Promise<Board> => {
    const response = await api.post('/boards', data)
    return response.data
  },

  updateBoard: async (boardId: string, data: Partial<CreateBoardRequest>): Promise<Board> => {
    const response = await api.patch(`/boards/${boardId}`, data)
    return response.data
  },

  deleteBoard: async (boardId: string): Promise<void> => {
    await api.delete(`/boards/${boardId}`)
  },
}

