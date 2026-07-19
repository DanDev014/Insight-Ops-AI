import type { FetchOptions } from 'ofetch'
import { request } from './request'

interface AuthCookieUser {
  id: number
  email: string
}

export async function authRequest<T>(
  event: Parameters<typeof getCookie>[0],
  buildRequest: (user: AuthCookieUser) => { endpoint: string; options?: FetchOptions },
): Promise<T> {
  const authCookieRaw = getCookie(event, 'auth_user')

  if (!authCookieRaw) {
    throw createError({ statusCode: 401, statusMessage: 'Not authenticated' })
  }

  let user: AuthCookieUser
  try {
    user = JSON.parse(authCookieRaw)
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Invalid session' })
  }

  const { endpoint, options } = buildRequest(user)

  return await request<T>(endpoint, options)
}