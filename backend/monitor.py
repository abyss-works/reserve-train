"""
monitor.py — 취소표 자동 예매 모니터링 엔진 (DB 기반)

DB에 저장된 태스크를 10초 간격으로 스캔하여
각 태스크의 interval_sec마다 재조회 → 좌석 발생 시 자동 예약.
"""
import threading
import time
import uuid

from ktx import KorailClient, KorailClientError, AuthError, SoldOut
from db import (
    create_task as db_create_task,
    get_active_tasks,
    update_task_status,
    delete_task as db_delete_task,
    get_tasks_by_session,
    get_task,
    get_logs,
    add_log,
    init_pool,
)


def start_task(task_data: dict) -> str:
    task_id = uuid.uuid4().hex
    task_data["task_id"] = task_id
    task_data["interval_sec"] = task_data.get("interval_sec", 30)
    db_create_task(task_data)
    add_log(task_id, "info", "자동 예매가 등록되었습니다")
    return task_id


def stop_task(task_id: str):
    t = get_task(task_id)
    if t:
        update_task_status(task_id, status="stopped", error_msg="사용자 중지")
        add_log(task_id, "info", "사용자가 자동 예매를 중지했습니다")


def list_tasks(session_id: str) -> list[dict]:
    return get_tasks_by_session(session_id)


def list_logs(task_id: str, limit: int = 50) -> list[dict]:
    return get_logs(task_id, limit)


# ─── 엔진 ────────────────────────────────────────


class MonitorEngine:
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        init_pool()
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        """10초 간격으로 DB에서 active 태스크를 읽어 체크"""
        while self._running:
            try:
                tasks = get_active_tasks()
                now = time.time()
                for t in tasks:
                    task_id = t["task_id"]
                    interval = t.get("interval_sec", 30)

                    # interval 체크: updated_at 기준 interval 경과 확인
                    updated = t["updated_at"]
                    if updated:
                        elapsed = now - updated.timestamp()
                        if elapsed < interval:
                            continue

                    try:
                        self._check(t)
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(10)

    def _check(self, task: dict):
        task_id = task["task_id"]

        client = KorailClient()
        try:
            client.login(task["korail_id"], task["korail_pw"])
        except (AuthError, KorailClientError) as e:
            add_log(task_id, "error", f"로그인 실패: {e}")
            update_task_status(task_id, check_count=task["check_count"] + 1, error_msg=str(e))
            # 로그인 실패 시 10분 후 재시도 (interval 유지)
            return

        try:
            trains = client.search(
                dep=task["dep"], arr=task["arr"],
                date=task["date"], time=task["time"],
                train_type=task["train_type"],
                include_no_seats=True,
            )
        except (AuthError, KorailClientError) as e:
            add_log(task_id, "error", f"조회 실패: {e}")
            update_task_status(task_id, check_count=task["check_count"] + 1, error_msg=str(e))
            return

        # 대상 열차 찾기 (general_available 우선)
        target = None
        for t in trains:
            if t.train_no == task["train_no"] and t.general_available:
                target = t
                break

        if target is None:
            # 좌석 없음 → count만 올리고 로그 없이 대기
            update_task_status(task_id, check_count=task["check_count"] + 1, error_msg="")
            # 주기적 상태 알림 (50회마다)
            if (task["check_count"] + 1) % 50 == 0:
                add_log(task_id, "info", f"{task['check_count'] + 1}회 확인 중... 계속 모니터링 중")
            return

        # 좌석 생김 → 예약 시도
        try:
            rsv = client.reserve(
                target,
                seat_option=task["seat_option"],
                try_waiting=task["try_waiting"],
            )
        except (SoldOut, AuthError, KorailClientError) as e:
            add_log(task_id, "error", f"예약 실패: {e}")
            update_task_status(
                task_id,
                check_count=task["check_count"] + 1,
                error_msg=f"예약 실패: {e}",
            )
            # 실패해도 계속 모니터링 (retry)
            return

        # 예약 성공
        result_data = {
            "rsv_id": rsv.rsv_id,
            "train_type": rsv.train_type,
            "train_no": rsv.train_no,
            "dep_name": rsv.dep_name,
            "dep_display": rsv.dep_display,
            "arr_name": rsv.arr_name,
            "arr_display": rsv.arr_display,
            "price": rsv.price,
            "seat_count": rsv.seat_count,
            "limit_display": rsv.limit_display,
        }
        update_task_status(
            task_id,
            status="reserved",
            check_count=task["check_count"] + 1,
            result=result_data,
            error_msg="",
        )
        add_log(task_id, "success", f"예약 성공! {rsv.rsv_id} ({rsv.price}원)")


# 싱글톤
_engine = MonitorEngine()
_engine.start()


def get_engine() -> MonitorEngine:
    return _engine
