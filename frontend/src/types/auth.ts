export type UserRole = 'admin' | 'teacher' | 'student'

export interface AuthUser {
  id: number
  username: string
  display_name: string
  role: UserRole | string
  aircraft_limit: number
}

export interface AuthSessionResponse {
  user: AuthUser
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  display_name: string
  password: string
}
