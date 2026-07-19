import type { FetchOptions } from 'ofetch'

export async function request<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const config = useRuntimeConfig()

  try {
    return await $fetch<T>(endpoint, {
      baseURL: config.flaskApiBaseUrl,
      ...options,
    })
  } catch (error: any) {
    console.error(`[BFF] ${endpoint}`, error)

    throw createError({
      statusCode: error?.statusCode || 500,
      statusMessage:
        error?.statusMessage || 'An unexpected error occurred.',
    })
  }
}