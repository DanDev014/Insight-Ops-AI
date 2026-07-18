import { request } from '~~/server/utils/request'

export default defineEventHandler(async () => {
  return await request('/projects')
})