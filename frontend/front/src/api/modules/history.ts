import request from '../request'

import type {
  ApiResponse,
  HistoryDeleteData,
  HistoryDetailData,
  HistoryListData,
  HistoryListQuery,
} from '../types'

export async function fetchHistoryList(params: HistoryListQuery): Promise<HistoryListData> {
  const { data } = await request.get<ApiResponse<HistoryListData>>('/api/history', { params })
  return data.data
}

export async function fetchHistoryDetail(historyId: number): Promise<HistoryDetailData> {
  const { data } = await request.get<ApiResponse<HistoryDetailData>>(`/api/history/${historyId}`)
  return data.data
}

export async function deleteHistory(historyId: number): Promise<HistoryDeleteData> {
  const { data } = await request.delete<ApiResponse<HistoryDeleteData>>(`/api/history/${historyId}`)
  return data.data
}
