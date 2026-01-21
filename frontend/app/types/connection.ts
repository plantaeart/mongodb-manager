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
