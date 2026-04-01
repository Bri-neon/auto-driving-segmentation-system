import request from '../request'

import type { ApiResponse, ModelInfo, ModelKey } from '../types'

export async function fetchModelInfo(modelKey: ModelKey): Promise<ModelInfo> {
  const { data } = await request.get<ApiResponse<ModelInfo>>('/api/model/info', {
    params: { model_key: modelKey },
  })

  return data.data
}
