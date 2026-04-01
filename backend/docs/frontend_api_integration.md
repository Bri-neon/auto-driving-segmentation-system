# Frontend API Integration (Auth + History)

## 1. Base Info

- Base URL: `http://127.0.0.1:8000`
- API Prefix: `/api`
- Auth Mode: `Bearer JWT`
- Static Prefix: `/static`

All business responses use this shape:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

When `code != 0` or HTTP status is not `2xx`, treat as failed request.

---

## 2. Auth Flow

1. `POST /api/auth/register` register account
2. `POST /api/auth/login` get `access_token`
3. Use `Authorization: Bearer <access_token>` for protected APIs
4. `GET /api/auth/me` to refresh current user profile in frontend state

Token default expiry is controlled by backend config `JWT_EXPIRE_MINUTES` (current default: `120`).

---

## 3. Auth APIs

### 3.1 Register

- Method: `POST`
- URL: `/api/auth/register`
- Body (JSON):

```json
{
  "username": "alice_01",
  "password": "AlicePass@123",
  "email": "alice@example.com",
  "nickname": "Alice"
}
```

- Success HTTP: `201`
- `data`:

```json
{
  "user": {
    "id": 2,
    "username": "alice_01",
    "email": "alice@example.com",
    "nickname": "Alice",
    "avatar_url": null,
    "role": "user",
    "is_active": true,
    "created_at": "2026-04-01T18:00:00",
    "last_login_at": null
  }
}
```

### 3.2 Login

- Method: `POST`
- URL: `/api/auth/login`
- Body (JSON):

```json
{
  "username": "alice_01",
  "password": "AlicePass@123"
}
```

- Success HTTP: `200`
- `data`:

```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 7200,
  "user": {
    "id": 2,
    "username": "alice_01",
    "email": "alice@example.com",
    "nickname": "Alice",
    "avatar_url": "/static/avatar/u2_avatar_xxx.png",
    "role": "user",
    "is_active": true,
    "created_at": "2026-04-01T18:00:00",
    "last_login_at": "2026-04-01T18:10:00"
  }
}
```

### 3.3 Get Current User

- Method: `GET`
- URL: `/api/auth/me`
- Header: `Authorization: Bearer <jwt>`

### 3.4 Upload Avatar

- Method: `POST`
- URL: `/api/auth/avatar`
- Header: `Authorization: Bearer <jwt>`
- Body: `multipart/form-data`
  - `file`: image file (`jpg/jpeg/png`)

- `data`:

```json
{
  "avatar_url": "/static/avatar/u2_avatar_xxx.png"
}
```

### 3.5 Update My Profile

- Method: `PUT`
- URL: `/api/auth/me/profile`
- Header: `Authorization: Bearer <jwt>`
- Body (JSON):

```json
{
  "email": "alice_new@example.com",
  "nickname": "Alice New"
}
```

- `data`:

```json
{
  "user": {
    "id": 2,
    "username": "alice_01",
    "email": "alice_new@example.com",
    "nickname": "Alice New",
    "avatar_url": "/static/avatar/u2_avatar_xxx.png",
    "role": "user",
    "is_active": true,
    "created_at": "2026-04-01T18:00:00",
    "last_login_at": "2026-04-01T18:10:00"
  }
}
```

### 3.6 Change My Password

- Method: `PUT`
- URL: `/api/auth/me/password`
- Header: `Authorization: Bearer <jwt>`
- Body (JSON):

```json
{
  "current_password": "AlicePass@123",
  "new_password": "AlicePass@456"
}
```

- `data`:

```json
{
  "changed": true
}
```

---

## 4. Segment APIs (Now Protected)

The following APIs require login now:

- `POST /api/segment`
- `POST /api/segment/video`
- `POST /api/segment/video/realtime`
- `POST /api/segment/video/finalize/{task_id}`
- `GET /api/segment/video/result/{task_id}`
- `WS /api/segment/video/ws/{task_id}`

Public API remains:

- `GET /api/segment/resolutions`

### 4.1 WebSocket Auth Change

Realtime WS now must carry token in query:

```text
ws://127.0.0.1:8000/api/segment/video/ws/{task_id}?token=<jwt>
```

If token missing/invalid, backend will close socket with code `1008`.

---

## 5. History APIs

### 5.1 List History (Paged)

- Method: `GET`
- URL: `/api/history?page=1&page_size=20&request_type=image&process_mode=sync`
- Header: `Authorization: Bearer <jwt>`
- Query params:
  - `page` (default 1)
  - `page_size` (default 20, max 100)
  - `request_type`: `image` | `video` (optional)
  - `process_mode`: `sync` | `realtime` (optional)

- `data`:

```json
{
  "total": 12,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 18,
      "user_id": 2,
      "user_username": null,
      "user_nickname": null,
      "task_id": "8d20...",
      "request_type": "video",
      "process_mode": "realtime",
      "model_key": "bisenetv2",
      "model_name": "BiSeNetV2 FP16",
      "resolution": "256x512",
      "original_url": "/static/upload/u2_rt_xxx.mp4",
      "segmented_url": "/static/result/u2_rt_xxx_mask.mp4",
      "overlay_url": "/static/result/u2_rt_xxx_overlay.mp4",
      "realtime_status": "completed",
      "finalize_status": "completed",
      "status_message": null,
      "avg_fps": 15.2,
      "realtime_fps": 17.3,
      "inference_time": 0.0234,
      "classes": null,
      "created_at": "2026-04-01T18:20:00",
      "updated_at": "2026-04-01T18:21:10"
    }
  ]
}
```

### 5.2 History Detail

- Method: `GET`
- URL: `/api/history/{history_id}`
- Header: `Authorization: Bearer <jwt>`

### 5.3 Delete History

- Method: `DELETE`
- URL: `/api/history/{history_id}`
- Header: `Authorization: Bearer <jwt>`

Returns:

```json
{
  "id": 18,
  "deleted": true
}
```

---

## 6. Admin APIs (Admin Role Only)

All admin APIs require:

- Header: `Authorization: Bearer <admin_jwt>`
- User role: `admin`

### 6.1 List Users

- Method: `GET`
- URL: `/api/admin/users?page=1&page_size=20&keyword=alice&role=user&is_active=true`

### 6.2 Update User

- Method: `PATCH`
- URL: `/api/admin/users/{user_id}`
- Body (JSON):

```json
{
  "email": "alice_review@example.com",
  "nickname": "AliceReview",
  "role": "user",
  "is_active": true
}
```

### 6.3 Reset User Password

- Method: `PUT`
- URL: `/api/admin/users/{user_id}/password`
- Body (JSON):

```json
{
  "new_password": "Reset@123456"
}
```

### 6.4 List All Histories

- Method: `GET`
- URL: `/api/admin/histories?page=1&page_size=20&user_id=2&username=alice&request_type=video&process_mode=realtime`

### 6.5 Update Any History

- Method: `PATCH`
- URL: `/api/admin/histories/{history_id}`
- Body (JSON):

```json
{
  "realtime_status": "completed",
  "finalize_status": "completed",
  "status_message": "审核通过",
  "segmented_url": "/static/result/xxx_mask.mp4",
  "overlay_url": "/static/result/xxx_overlay.mp4"
}
```

### 6.6 Delete Any History

- Method: `DELETE`
- URL: `/api/admin/histories/{history_id}`

---

## 7. Frontend Notes

- Save token after login and inject to all protected HTTP requests.
- For realtime WS, append `token` in query string.
- History list should be user-scoped; backend already enforces owner isolation.
- Personal page can call `/api/auth/me/profile` and `/api/auth/me/password`.
- Show admin entry only when `user.role === "admin"` and call `/api/admin/*`.
- For media preview, use `baseURL + returned_url` (example: `http://127.0.0.1:8000/static/result/...`).
- For realtime history:
  - `realtime_status`: lifecycle of realtime stage
  - `finalize_status`: lifecycle of final video generation stage

---

## 8. Error Handling Suggestions

Common statuses:

- `401`: not logged in / token invalid / token expired
- `403`: user disabled or no permission
- `404`: resource not found (or not owned by current user)
- `409`: finalize called before realtime completed
- `413`: upload too large
- `415`: unsupported file type
- `422`: request validation failed

Suggested frontend behavior:

- On `401`: clear token + redirect login
- On `409`: keep polling realtime status then retry finalize
- On `413/415`: show user-friendly upload error directly
