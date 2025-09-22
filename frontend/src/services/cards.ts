import api from '@/lib/api'
import { Card, CreateCardRequest, MoveCardRequest, ReorderCardsRequest } from '@/types'

export const cardsApi = {
  createCard: async (data: CreateCardRequest): Promise<Card> => {
    const response = await api.post('/cards', data)
    return response.data
  },

  updateCard: async (cardId: string, data: Partial<CreateCardRequest>): Promise<Card> => {
    const response = await api.patch(`/cards/${cardId}`, data)
    return response.data
  },

  deleteCard: async (cardId: string): Promise<void> => {
    await api.delete(`/cards/${cardId}`)
  },

  moveCard: async (data: MoveCardRequest): Promise<Card> => {
    const response = await api.patch('/cards/move', data)
    return response.data
  },

  reorderCards: async (listId: string, positions: ReorderCardsRequest[]): Promise<void> => {
    await api.patch(`/cards/reorder?list_id=${listId}`, positions)
  },
}

