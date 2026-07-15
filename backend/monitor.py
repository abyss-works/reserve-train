"""
monitor.py — 취소표 자동 예매 모니터링 엔진

30초 간격으로 지정된 열차를 재조회하여 좌석 발생 시 자동 예약.
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from ktx import KorailClient, KorailClientError, AuthError, SoldOut


@dataclass
class MonitorTask:
    task_id: str
    session_id: str
    korail_id: str
    korail_pw: str
    dep: str
    arr: str
    date: str
    time: str
    train_type: str
    train_idx: int
    train_no: str
    train_label: str
    seat_option: str = "general-first"
    try_waiting: bool = False
    status: str = "monitoring"  # monitoring | reserved | failed | stopped
    check_count: int = 0
    error_msg: str = ""
    result: dict = field(default_factory=dict)


class MonitorEngine:
    """백그라운드 모니터링 엔진 (싱글 스레드, 30초 간격)"""

    def __init__(self):
        self._tasks: dict[str, MonitorTask] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def add_task(self, task: MonitorTask) -> str:
        with self._lock:
            self._tasks[task.task_id] = task
        if not self._running:
            self.start()
        return task.task_id

    def remove_task(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.pop(task_id, None)
            if t:
                t.status = "stopped"
            return t is not None

    def get_task(self, task_id: str) -> Optional[MonitorTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_tasks(self) -> list[MonitorTask]:
        with self._lock:
            return list(self._tasks.values())

    def get_tasks_by_session(self, session_id: str) -> list[MonitorTask]:
        with self._lock:
            return [t for t in self._tasks.values() if t.session_id == session_id]

    def _loop(self):
        while self._running:
            tasks = self.get_tasks()
            for task in tasks:
                if task.status != "monitoring":
                    continue
                try:
                    self._check(task)
                except Exception:
                    pass
            time.sleep(30)

    def _check(self, task: MonitorTask):
        """단일 태스크 체크"""
        client = KorailClient()
        try:
            client.login(task.korail_id, task.korail_pw)
        except (AuthError, KorailClientError) as e:
            with self._lock:
                task.check_count += 1
                task.error_msg = f"로그인 실패: {e}"
            return

        try:
            trains = client.search(
                dep=task.dep, arr=task.arr,
                date=task.date, time=task.time,
                train_type=task.train_type,
                include_no_seats=True,
            )
        except (AuthError, KorailClientError) as e:
            with self._lock:
                task.check_count += 1
                task.error_msg = f"조회 실패: {e}"
            return

        with self._lock:
            task.check_count += 1

        # 대상 열차 찾기
        target = None
        for t in trains:
            if t.train_no == task.train_no and t.general_available:
                target = t
                break

        if target is None:
            return  # 아직 좌석 없음

        # 좌석 생김 → 예약 시도
        try:
            rsv = client.reserve(target, seat_option=task.seat_option, try_waiting=task.try_waiting)
            with self._lock:
                task.status = "reserved"
                task.result = {
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
        except (SoldOut, AuthError, KorailClientError) as e:
            with self._lock:
                task.error_msg = f"예약 실패: {e}"


# 싱글톤
_engine = MonitorEngine()
_engine.start()


def get_engine() -> MonitorEngine:
    return _engine
