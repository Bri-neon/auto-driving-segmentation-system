import request from '../request'

import type {
  AdminHistoryListQuery,
  AdminHistoryUpdatePayload,
  AdminUserDetailData,
  AdminUserListData,
  AdminUserListQuery,
  AdminUserPasswordResetData,
  AdminUserPasswordResetPayload,
  AdminUserUpdatePayload,
  ApiResponse,
  HistoryDeleteData,
  HistoryDetailData,
  HistoryListData,
} from '../types'

export async function fetchAdminUsers(params: AdminUserListQuery): Promise<AdminUserListData> {
  const { data } = await request.get<ApiResponse<AdminUserListData>>('/api/admin/users', { params })
  return data.data
}

export async function fetchAdminUserDetail(userId: number): Promise<AdminUserDetailData> {
  const { data } = await request.get<ApiResponse<AdminUserDetailData>>(`/api/admin/users/${userId}`)
  return data.data
}

export async function updateAdminUser(userId: number, payload: AdminUserUpdatePayload): Promise<AdminUserDetailData> {
  const { data } = await request.patch<ApiResponse<AdminUserDetailData>>(`/api/admin/users/${userId}`, payload)
  return data.data
}

export async function resetAdminUserPassword(
  userId: number,
  payload: AdminUserPasswordResetPayload,
): Promise<AdminUserPasswordResetData> {
  const { data } = await request.put<ApiResponse<AdminUserPasswordResetData>>(`/api/admin/users/${userId}/password`, payload)
  return data.data
}

export async function fetchAdminHistories(params: AdminHistoryListQuery): Promise<HistoryListData> {
  const { data } = await request.get<ApiResponse<HistoryListData>>('/api/admin/histories', { params })
  return data.data
}

export async function fetchAdminHistoryDetail(historyId: number): Promise<HistoryDetailData> {
  const { data } = await request.get<ApiResponse<HistoryDetailData>>(`/api/admin/histories/${historyId}`)
  return data.data
}

export async function updateAdminHistory(historyId: number, payload: AdminHistoryUpdatePayload): Promise<HistoryDetailData> {
  const { data } = await request.patch<ApiResponse<HistoryDetailData>>(`/api/admin/histories/${historyId}`, payload)
  return data.data
}

export async function deleteAdminHistory(historyId: number): Promise<HistoryDeleteData> {
  const { data } = await request.delete<ApiResponse<HistoryDeleteData>>(`/api/admin/histories/${historyId}`)
  return data.data
}
