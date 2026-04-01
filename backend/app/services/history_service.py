from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from app.core.database import db_cursor, fetch_one_dict
from app.core.exceptions import AppException


class InferenceHistoryService:
    def create_image_history(
        self,
        user_id: int,
        model_key: str,
        model_name: str,
        resolution: str,
        original_url: str,
        segmented_url: str,
        overlay_url: str,
        inference_time: float,
        classes: list[dict[str, Any]] | None,
    ) -> int:
        classes_json = json.dumps(classes or [], ensure_ascii=False)
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO inference_histories (
                    user_id, request_type, process_mode, model_key, model_name, resolution,
                    original_url, segmented_url, overlay_url,
                    realtime_status, finalize_status, inference_time, classes_json
                ) VALUES (%s, 'image', 'sync', %s, %s, %s, %s, %s, %s, 'completed', 'completed', %s, %s)
                """,
                (
                    user_id,
                    model_key,
                    model_name,
                    resolution,
                    original_url,
                    segmented_url,
                    overlay_url,
                    inference_time,
                    classes_json,
                ),
            )
            return int(cursor.lastrowid)

    def create_video_history(
        self,
        user_id: int,
        model_key: str,
        model_name: str,
        resolution: str,
        original_url: str,
        segmented_url: str,
        overlay_url: str,
        avg_fps: float,
        realtime_fps: float,
        inference_time: float,
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO inference_histories (
                    user_id, request_type, process_mode, model_key, model_name, resolution,
                    original_url, segmented_url, overlay_url,
                    realtime_status, finalize_status, avg_fps, realtime_fps, inference_time
                ) VALUES (%s, 'video', 'sync', %s, %s, %s, %s, %s, %s, 'completed', 'completed', %s, %s, %s)
                """,
                (
                    user_id,
                    model_key,
                    model_name,
                    resolution,
                    original_url,
                    segmented_url,
                    overlay_url,
                    avg_fps,
                    realtime_fps,
                    inference_time,
                ),
            )
            return int(cursor.lastrowid)

    def create_realtime_task_history(
        self,
        user_id: int,
        task_id: str,
        model_key: str,
        model_name: str,
        resolution: str,
        original_url: str,
        segmented_url: str,
        overlay_url: str,
        realtime_status: str,
        finalize_status: str,
    ) -> int:
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO inference_histories (
                    user_id, task_id, request_type, process_mode, model_key, model_name, resolution,
                    original_url, segmented_url, overlay_url,
                    realtime_status, finalize_status
                ) VALUES (%s, %s, 'video', 'realtime', %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    model_key = VALUES(model_key),
                    model_name = VALUES(model_name),
                    resolution = VALUES(resolution),
                    original_url = VALUES(original_url),
                    segmented_url = VALUES(segmented_url),
                    overlay_url = VALUES(overlay_url),
                    realtime_status = VALUES(realtime_status),
                    finalize_status = VALUES(finalize_status)
                """,
                (
                    user_id,
                    task_id,
                    model_key,
                    model_name,
                    resolution,
                    original_url,
                    segmented_url,
                    overlay_url,
                    realtime_status,
                    finalize_status,
                ),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            cursor.execute("SELECT id FROM inference_histories WHERE task_id = %s LIMIT 1", (task_id,))
            row = fetch_one_dict(cursor)
            return int(row["id"]) if row else 0

    def update_task_history(
        self,
        task_id: str,
        realtime_status: str | None = None,
        finalize_status: str | None = None,
        status_message: str | None = None,
        avg_fps: float | None = None,
        realtime_fps: float | None = None,
        inference_time: float | None = None,
        segmented_url: str | None = None,
        overlay_url: str | None = None,
    ) -> None:
        updates: dict[str, Any] = {}
        if realtime_status is not None:
            updates["realtime_status"] = realtime_status
        if finalize_status is not None:
            updates["finalize_status"] = finalize_status
        if status_message is not None:
            updates["status_message"] = status_message[:255]
        if avg_fps is not None:
            updates["avg_fps"] = avg_fps
        if realtime_fps is not None:
            updates["realtime_fps"] = realtime_fps
        if inference_time is not None:
            updates["inference_time"] = inference_time
        if segmented_url is not None:
            updates["segmented_url"] = segmented_url
        if overlay_url is not None:
            updates["overlay_url"] = overlay_url

        if not updates:
            return

        set_clause = ", ".join(f"{field} = %s" for field in updates.keys())
        params = list(updates.values()) + [task_id]

        with db_cursor() as cursor:
            cursor.execute(
                f"UPDATE inference_histories SET {set_clause} WHERE task_id = %s",  # nosec B608
                tuple(params),
            )

    def list_user_histories(
        self,
        user_id: int,
        page: int,
        page_size: int,
        request_type: str | None = None,
        process_mode: str | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        filters = ["h.user_id = %s"]
        params: list[Any] = [user_id]

        if request_type:
            filters.append("h.request_type = %s")
            params.append(request_type)
        if process_mode:
            filters.append("h.process_mode = %s")
            params.append(process_mode)

        where_clause = " AND ".join(filters)
        return self._list_histories(
            where_clause=where_clause,
            params=params,
            page=page,
            page_size=page_size,
            include_user_meta=False,
        )

    def list_admin_histories(
        self,
        *,
        page: int,
        page_size: int,
        request_type: str | None = None,
        process_mode: str | None = None,
        user_id: int | None = None,
        username: str | None = None,
    ) -> tuple[int, list[dict[str, Any]]]:
        filters = ["1=1"]
        params: list[Any] = []

        if request_type:
            filters.append("h.request_type = %s")
            params.append(request_type)
        if process_mode:
            filters.append("h.process_mode = %s")
            params.append(process_mode)
        if user_id is not None:
            filters.append("h.user_id = %s")
            params.append(user_id)
        if username:
            kw = username.strip()
            if kw:
                filters.append("u.username LIKE %s")
                params.append(f"%{kw}%")

        where_clause = " AND ".join(filters)
        return self._list_histories(
            where_clause=where_clause,
            params=params,
            page=page,
            page_size=page_size,
            include_user_meta=True,
        )

    def get_user_history(self, user_id: int, history_id: int) -> dict[str, Any] | None:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    h.id, h.user_id, h.task_id, h.request_type, h.process_mode, h.model_key, h.model_name, h.resolution,
                    h.original_url, h.segmented_url, h.overlay_url,
                    h.realtime_status, h.finalize_status, h.status_message,
                    h.avg_fps, h.realtime_fps, h.inference_time, h.classes_json,
                    h.created_at, h.updated_at
                FROM inference_histories h
                WHERE h.id = %s AND h.user_id = %s
                LIMIT 1
                """,
                (history_id, user_id),
            )
            row = fetch_one_dict(cursor)
        if row is None:
            return None
        return self._normalize_row(row)

    def get_history_by_id(self, history_id: int, *, include_user_meta: bool = False) -> dict[str, Any] | None:
        if include_user_meta:
            sql = """
                SELECT
                    h.id, h.user_id, h.task_id, h.request_type, h.process_mode, h.model_key, h.model_name, h.resolution,
                    h.original_url, h.segmented_url, h.overlay_url,
                    h.realtime_status, h.finalize_status, h.status_message,
                    h.avg_fps, h.realtime_fps, h.inference_time, h.classes_json,
                    h.created_at, h.updated_at,
                    u.username AS user_username,
                    u.nickname AS user_nickname
                FROM inference_histories h
                JOIN users u ON u.id = h.user_id
                WHERE h.id = %s
                LIMIT 1
            """
        else:
            sql = """
                SELECT
                    h.id, h.user_id, h.task_id, h.request_type, h.process_mode, h.model_key, h.model_name, h.resolution,
                    h.original_url, h.segmented_url, h.overlay_url,
                    h.realtime_status, h.finalize_status, h.status_message,
                    h.avg_fps, h.realtime_fps, h.inference_time, h.classes_json,
                    h.created_at, h.updated_at
                FROM inference_histories h
                WHERE h.id = %s
                LIMIT 1
            """
        with db_cursor() as cursor:
            cursor.execute(sql, (history_id,))
            row = fetch_one_dict(cursor)
        if row is None:
            return None
        return self._normalize_row(row)

    def delete_user_history(self, user_id: int, history_id: int) -> bool:
        with db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM inference_histories WHERE id = %s AND user_id = %s",
                (history_id, user_id),
            )
            return cursor.rowcount > 0

    def delete_history_by_id(self, history_id: int) -> bool:
        with db_cursor() as cursor:
            cursor.execute("DELETE FROM inference_histories WHERE id = %s", (history_id,))
            return cursor.rowcount > 0

    def admin_update_history(self, history_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {"realtime_status", "finalize_status", "status_message", "segmented_url", "overlay_url"}
        db_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if "status_message" in db_updates and db_updates["status_message"] is not None:
            db_updates["status_message"] = str(db_updates["status_message"])[:255]

        if not db_updates:
            raise AppException("缺少可更新字段")

        set_clause = ", ".join(f"{field} = %s" for field in db_updates.keys())
        params = list(db_updates.values()) + [history_id]

        with db_cursor() as cursor:
            cursor.execute(
                f"UPDATE inference_histories SET {set_clause} WHERE id = %s",  # nosec B608
                tuple(params),
            )

        return self.get_history_by_id(history_id, include_user_meta=True)

    def _list_histories(
        self,
        *,
        where_clause: str,
        params: list[Any],
        page: int,
        page_size: int,
        include_user_meta: bool,
    ) -> tuple[int, list[dict[str, Any]]]:
        offset = (page - 1) * page_size

        count_from = "inference_histories h"
        query_from = "inference_histories h"
        user_select = ""
        if include_user_meta:
            count_from = "inference_histories h JOIN users u ON u.id = h.user_id"
            query_from = "inference_histories h JOIN users u ON u.id = h.user_id"
            user_select = ", u.username AS user_username, u.nickname AS user_nickname"

        with db_cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM {count_from} WHERE {where_clause}",  # nosec B608
                tuple(params),
            )
            total_row = fetch_one_dict(cursor) or {"total": 0}
            total = int(total_row.get("total", 0))

            cursor.execute(
                f"""
                SELECT
                    h.id, h.user_id, h.task_id, h.request_type, h.process_mode, h.model_key, h.model_name, h.resolution,
                    h.original_url, h.segmented_url, h.overlay_url,
                    h.realtime_status, h.finalize_status, h.status_message,
                    h.avg_fps, h.realtime_fps, h.inference_time, h.classes_json,
                    h.created_at, h.updated_at
                    {user_select}
                FROM {query_from}
                WHERE {where_clause}
                ORDER BY h.created_at DESC
                LIMIT %s OFFSET %s
                """,  # nosec B608
                tuple(params + [page_size, offset]),
            )
            rows = [self._normalize_row(dict(row)) for row in cursor.fetchall()]

        return total, rows

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        classes_json = row.pop("classes_json", None)
        row["classes"] = None
        if classes_json:
            try:
                row["classes"] = json.loads(classes_json)
            except (TypeError, ValueError):
                row["classes"] = None

        for key in ("avg_fps", "realtime_fps", "inference_time"):
            value = row.get(key)
            if isinstance(value, Decimal):
                row[key] = float(value)

        row["id"] = int(row["id"])
        row["user_id"] = int(row["user_id"])
        return row


inference_history_service = InferenceHistoryService()
