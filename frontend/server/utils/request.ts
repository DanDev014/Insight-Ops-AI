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

    const flaskMessage = error?.data?.error

    throw createError({
      statusCode: error?.statusCode || error?.status || 500,
      statusMessage: flaskMessage || 'An unexpected error occurred.',
      data: error?.data,
    })
  }
}