import api from '@/lib/api'
import { List, CreateListRequest, ReorderCardsRequest } from '@/types'

export const listsApi = {
  createList: async (data: CreateListRequest): Promise<List> => {
    const response = await api.post('/lists', data)
    return response.data
  },

  updateList: async (listId: string, data: Partial<CreateListRequest>): Promise<List> => {
    const response = await api.patch(`/lists/${listId}`, data)
    return response.data
  },

  deleteList: async (listId: string): Promise<void> => {
    await api.delete(`/lists/${listId}`)
  },

  reorderLists: async (boardId: string, positions: ReorderCardsRequest[]): Promise<void> => {
    await api.patch(`/lists/reorder?board_id=${boardId}`, positions)
  },
}

