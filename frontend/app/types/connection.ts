import { MongoConnectionStatus } from '~/enums'

export interface Connection {
  name: string
  uri: string
  status?: MongoConnectionStatus
  created_at?: string
}

export interface ConnectionCreate {
  name: string
  uri: string
}

export interface ConnectionUpdate {
  uri?: string
}

export interface ConnectionDetails {
  name: string
  uri: string
  description?: string
  host?: string
  port?: number
  username?: string
  password?: string
  database?: string
  auth_source?: string
}
