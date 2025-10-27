import api from '@/lib-custom/api'

export interface Notification {
  id: string
  type: string
  title: string
  message: string
  data?: any
  is_read: boolean
  created_at: string
  read_at?: string
}

export interface NotificationResponse {
  count: number
}

export const notificationsApi = {
  getNotifications: async (skip = 0, limit = 50): Promise<Notification[]> => {
    const response = await api.get(`/notifications?skip=${skip}&limit=${limit}`)
    return response.data
  },

  getUnreadCount: async (): Promise<NotificationResponse> => {
    const response = await api.get('/notifications/unread-count')
    return response.data
  },

  markAsRead: async (notificationId: string): Promise<Notification> => {
    const response = await api.patch(`/notifications/${notificationId}/read`)
    return response.data
  },

  markAllAsRead: async (): Promise<{ message: string }> => {
    const response = await api.patch('/notifications/mark-all-read')
    return response.data
  },

  deleteNotification: async (notificationId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/notifications/${notificationId}`)
    return response.data
  }
}
