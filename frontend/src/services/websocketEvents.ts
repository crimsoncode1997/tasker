export type BoardEvent = 
  | { event_type: 'card_moved' | 'card_created' | 'card_updated' | 'card_deleted'; card: any }
  | { event_type: 'list_reordered' | 'list_created'; lists: any[] }
  | { event_type: 'member_invited'; member: any }
  | { event_type: 'init'; board: any }

export type NotificationEvent =
  | { event_type: 'board_invite'; board: any; inviter: any }
  | { event_type: 'init'; notifications: any[] }
