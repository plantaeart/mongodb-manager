export interface Connection {
  name: string
  uri: string
  status?: 'connected' | 'disconnected'
  created_at?: string
}

export interface ConnectionCreate {
  name: string
  uri: string
}

export interface ConnectionUpdate {
  uri?: string
}
