import { http } from '@/utils/request'

export const aiApi = {
  generate(payload) {
    return http.post('/ai/generate', payload)
  }
}
