export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Board {
  id: string
  title: string
  description?: string
  owner_id: string
  created_at: string
  updated_at: string
  owner: User
  lists: List[]
}

export interface List {
  id: string
  title: string
  board_id: string
  position: number
  created_at: string
  updated_at: string
  cards: Card[]
}

export interface Card {
  id: string
  title: string
  description?: string
  list_id: string
  position: number
  assignee_id?: string
  due_date?: string
  created_at: string
  updated_at: string
  assignee?: User
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface CreateBoardRequest {
  title: string
  description?: string
}

export interface CreateListRequest {
  title: string
  board_id: string
  position?: number
}

export interface CreateCardRequest {
  title: string
  description?: string
  list_id: string
  position?: number
  assignee_id?: string
  due_date?: string
}

export interface MoveCardRequest {
  card_id: string
  list_id: string
  position: number
}

export interface ReorderCardsRequest {
  card_id: string
  position: number
}[]

