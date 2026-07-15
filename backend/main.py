"""
main.py — FastAPI 앱 + 정적파일 서빙

Korail KTX 예매 API 서버. Vue SPA 정적파일을 함께 서빙한다.
"""
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ktx import (
    KorailClient, AuthError, NoResults, SoldOut, NetworkError, KorailClientError,
)

# ─── 세션 저장소 (in-memory) ─────────────────────────────

_sessions: dict[str, KorailClient] = {}


def _get_client(session_id: str | None) -> KorailClient:
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return _sessions[session_id]


# ─── 요청/응답 모델 ──────────────────────────────────────


class LoginRequest(BaseModel):
    id: str
    password: str


class SearchParams(BaseModel):
    dep: str = "서울"
    arr: str = "부산"
    date: str = ""
    time: str = ""
    train_type: str = "ktx"
    include_no_seats: bool = False
    include_waiting_list: bool = False


class ReserveRequest(BaseModel):
    train_idx: int = 0
    seat_option: str = "general-first"
    try_waiting: bool = False


class CancelRequest(BaseModel):
    reservation_idx: int = 0


# ─── 애플리케이션 ────────────────────────────────────────

static_dir = Path(__file__).resolve().parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="KTX 예매 도우미", version="0.1.0", lifespan=lifespan)


# ─── API 라우트 ──────────────────────────────────────────


@app.post("/api/v1/login")
def login(req: LoginRequest):
    """Korail 로그인"""
    client = KorailClient()
    try:
        name = client.login(req.id, req.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except KorailClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

    session_id = uuid.uuid4().hex
    _sessions[session_id] = client
    return {"session_id": session_id, "name": name}


@app.post("/api/v1/logout")
def logout(session_id: str = ""):
    """로그아웃"""
    _sessions.pop(session_id, None)
    return {"success": True}


@app.get("/api/v1/stations")
def get_stations():
    """코레일 역 목록 조회"""
    import requests
    try:
        resp = requests.get(
            "https://smart.letskorail.com/classes/com.korail.mobile.common.stationdata",
            timeout=10,
        )
        data = resp.json()
        stns = data.get("stns", {}).get("stn", [])
        return {
            "stations": [
                {"name": s["stn_nm"], "code": s["stn_cd"]}
                for s in stns
                if s.get("stn_nm")
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"역 정보 조회 실패: {e}")


@app.get("/api/v1/search")
def search_trains(
    dep: str = "서울",
    arr: str = "부산",
    date: str = "",
    time: str = "",
    train_type: str = "ktx",
    include_no_seats: bool = True,
    include_waiting_list: bool = False,
    session_id: str = "",
):
    """열차 조회"""
    client = _get_client(session_id)
    try:
        trains = client.search(
            dep=dep, arr=arr, date=date or None, time=time or None,
            train_type=train_type,
            include_no_seats=include_no_seats,
            include_waiting_list=include_waiting_list,
        )
    except AuthError as e:
        _sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail=str(e))
    except NoResults as e:
        return {"trains": [], "message": str(e)}
    except KorailClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    result = []
    for i, t in enumerate(trains):
        result.append({
            "idx": i,
            "train_type": t.train_type,
            "train_no": t.train_no,
            "dep_name": t.dep_name,
            "arr_name": t.arr_name,
            "dep_date": t.dep_date,
            "dep_time": t.dep_time,
            "arr_time": t.arr_time,
            "dep_display": t.dep_display,
            "arr_display": t.arr_display,
            "duration": t.duration,
            "general_available": t.general_available,
            "special_available": t.special_available,
            "waiting_possible": t.waiting_possible,
        })
    return {"trains": result}


@app.get("/api/v1/reservations")
def get_reservations(session_id: str = ""):
    """예약 내역 조회"""
    client = _get_client(session_id)
    try:
        rsvs = client.reservations()
    except AuthError as e:
        _sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail=str(e))
    except KorailClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    result = []
    for i, r in enumerate(rsvs):
        result.append({
            "idx": i,
            "rsv_id": r.rsv_id,
            "train_type": r.train_type,
            "train_no": r.train_no,
            "dep_name": r.dep_name,
            "arr_name": r.arr_name,
            "dep_time": r.dep_time,
            "arr_time": r.arr_time,
            "dep_display": r.dep_display,
            "arr_display": r.arr_display,
            "price": r.price,
            "seat_count": r.seat_count,
            "limit_display": r.limit_display,
        })
    return {"reservations": result}


@app.post("/api/v1/reserve")
def reserve_train(req: ReserveRequest, session_id: str = ""):
    """열차 예약"""
    client = _get_client(session_id)

    # search 결과에서 train_info를 다시 찾아야 함
    # 클라이언트가 마지막 검색 결과의 train_idx를 보내면,
    # 서버는 최신 검색 결과를 다시 가져와서 매칭
    # (실제로는 세션에 마지막 검색 결과를 저장해야 함)
    # 단순화: 클라이언트가 train_idx만 보내면 되는 구조

    # 세션에 마지막 search 결과를 저장
    last_trains = getattr(client, '_last_search_results', None)
    if not last_trains or req.train_idx >= len(last_trains):
        raise HTTPException(status_code=400, detail="열차 정보가 만료되었습니다. 다시 조회해주세요.")

    train = last_trains[req.train_idx]
    try:
        rsv = client.reserve(train, seat_option=req.seat_option, try_waiting=req.try_waiting)
    except AuthError as e:
        _sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail=str(e))
    except SoldOut as e:
        raise HTTPException(status_code=409, detail=str(e))
    except KorailClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "reservation": {
            "rsv_id": rsv.rsv_id,
            "train_type": rsv.train_type,
            "train_no": rsv.train_no,
            "dep_name": rsv.dep_name,
            "arr_name": rsv.arr_name,
            "dep_time": rsv.dep_time,
            "arr_time": rsv.arr_time,
            "dep_display": rsv.dep_display,
            "arr_display": rsv.arr_display,
            "price": rsv.price,
            "seat_count": rsv.seat_count,
            "limit_display": rsv.limit_display,
        }
    }


@app.post("/api/v1/cancel")
def cancel_reservation(req: CancelRequest, session_id: str = ""):
    """예약 취소"""
    client = _get_client(session_id)

    last_rsvs = getattr(client, '_last_reservations', None)
    if not last_rsvs or req.reservation_idx >= len(last_rsvs):
        raise HTTPException(status_code=400, detail="예약 정보가 만료되었습니다. 다시 조회해주세요.")

    try:
        client.cancel(last_rsvs[req.reservation_idx])
    except AuthError as e:
        _sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail=str(e))
    except KorailClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"success": True}


# ─── search/reserve 연동: search 결과를 세션에 저장 ──────

# search 호출 시 client에 마지막 결과를 저장하는 wrapper
_original_search = KorailClient.search


def _patched_search(self, *args, **kwargs):
    results = _original_search(self, *args, **kwargs)
    self._last_search_results = results
    return results


KorailClient.search = _patched_search

_original_reservations = KorailClient.reservations


def _patched_reservations(self):
    results = _original_reservations(self)
    self._last_reservations = results
    return results


KorailClient.reservations = _patched_reservations


# ─── 정적파일 서빙 ────────────────────────────────────

if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"error": "not found"}
else:
    @app.get("/")
    def root():
        return {"status": "API only", "message": "Frontend not built"}


# ─── 실행 ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
