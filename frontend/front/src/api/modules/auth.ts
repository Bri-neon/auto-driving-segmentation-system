import request from '../request'

import type {
  ApiResponse,
  AuthLoginData,
  AuthLoginPayload,
  AuthMeData,
  AuthRegisterData,
  AuthRegisterPayload,
  AvatarUploadData,
  PasswordChangeData,
  PasswordChangePayload,
  ProfileUpdateData,
  ProfileUpdatePayload,
} from '../types'

export async function registerUser(payload: AuthRegisterPayload): Promise<AuthRegisterData> {
  const { data } = await request.post<ApiResponse<AuthRegisterData>>('/api/auth/register', payload)
  return data.data
}

export async function loginUser(payload: AuthLoginPayload): Promise<AuthLoginData> {
  const { data } = await request.post<ApiResponse<AuthLoginData>>('/api/auth/login', payload)
  return data.data
}

export async function fetchCurrentUser(): Promise<AuthMeData> {
  const { data } = await request.get<ApiResponse<AuthMeData>>('/api/auth/me')
  return data.data
}

export async function updateMyProfile(payload: ProfileUpdatePayload): Promise<ProfileUpdateData> {
  const { data } = await request.put<ApiResponse<ProfileUpdateData>>('/api/auth/me/profile', payload)
  return data.data
}

export async function changeMyPassword(payload: PasswordChangePayload): Promise<PasswordChangeData> {
  const { data } = await request.put<ApiResponse<PasswordChangeData>>('/api/auth/me/password', payload)
  return data.data
}

export async function uploadAvatar(file: File): Promise<AvatarUploadData> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await request.post<ApiResponse<AvatarUploadData>>('/api/auth/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data.data
}
