"""
ktx.py — korail2 기반 KTX 예매 래퍼
"""
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from korail2 import Korail, KorailError, NeedToLoginError, NoResultsError, SoldOutError
from korail2.korail2 import TrainType, ReserveOption


# ─── 도메인 데이터 클래스 ───────────────────────────────────


@dataclass
class TrainInfo:
    train_type: str
    train_no: str
    dep_name: str
    arr_name: str
    dep_date: str
    dep_time: str
    arr_date: str
    arr_time: str
    general_available: bool
    special_available: bool
    waiting_possible: bool
    _raw: object = field(repr=False)

    @property
    def dep_display(self) -> str:
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self) -> str:
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def duration(self) -> str:
        h = int(self.arr_time[:2]) - int(self.dep_time[:2])
        m = int(self.arr_time[2:4]) - int(self.dep_time[2:4])
        if m < 0:
            h -= 1
            m += 60
        return f"{h}시간 {m}분"


@dataclass
class ReservationInfo:
    rsv_id: str
    train_type: str
    train_no: str
    dep_name: str
    arr_name: str
    dep_date: str
    dep_time: str
    arr_time: str
    price: int
    seat_count: int
    buy_limit_date: str
    buy_limit_time: str
    _raw: object = field(repr=False)

    @property
    def dep_display(self) -> str:
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self) -> str:
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def limit_display(self) -> str:
        m = int(self.buy_limit_date[4:6])
        d = int(self.buy_limit_date[6:])
        t = f"{self.buy_limit_time[:2]}:{self.buy_limit_time[2:4]}"
        return f"{m}월 {d}일 {t}"


# ─── 사용자 정의 예외 ────────────────────────────────────


class KorailClientError(Exception):
    pass


class AuthError(KorailClientError):
    pass


class NoResults(KorailClientError):
    pass


class SoldOut(KorailClientError):
    pass


class NetworkError(Exception):
    pass


# ─── 메인 클라이언트 ─────────────────────────────────────


class KorailClient:
    def __init__(self):
        self._korail: Optional[Korail] = None
        self._logged_in: bool = False
        self._user_name: str = ""

    @property
    def logged_in(self) -> bool:
        return self._logged_in and self._korail is not None

    @property
    def user_name(self) -> str:
        return self._user_name

    def login(self, korail_id: str, korail_pw: str) -> str:
        try:
            self._korail = Korail(korail_id, korail_pw, auto_login=True)
            self._logged_in = True
            self._user_name = self._korail.user_name if hasattr(self._korail, 'user_name') and self._korail.user_name else ""
            return self._user_name
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError(f"로그인 실패: {e}") from e
        except KorailError as e:
            self._logged_in = False
            msg = str(e)
            if "MACRO" in msg or "error" in msg.lower():
                raise AuthError(f"Korail 로그인 오류 (anti-bot 가능): {msg}") from e
            raise AuthError(f"Korail 오류: {msg}") from e
        except Exception as e:
            self._logged_in = False
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"네트워크 연결 실패: {e}") from e
            raise KorailClientError(f"알 수 없는 오류: {e}") from e

    def search(
        self,
        dep: str,
        arr: str,
        date: Optional[str] = None,
        time: Optional[str] = None,
        train_type: str = "ktx",
        include_no_seats: bool = False,
        include_waiting_list: bool = False,
    ) -> list[TrainInfo]:
        if not self._logged_in or self._korail is None:
            raise AuthError("로그인이 필요합니다")

        tt_map = {
            "ktx": TrainType.KTX, "ktx-sancheon": TrainType.KTX_SANCHEON,
            "itx-saemaeul": TrainType.ITX_SAEMAEUL, "itx-cheongchun": TrainType.ITX_CHEONGCHUN,
            "saemaeul": TrainType.SAEMAEUL, "mugunghwa": TrainType.MUGUNGHWA,
            "nuriro": TrainType.NURIRO, "airport": TrainType.AIRPORT, "all": TrainType.ALL,
        }
        tt_code = tt_map.get(train_type.lower(), TrainType.KTX)
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        if not time:
            time = "000000"

        try:
            trains = self._korail.search_train(
                dep, arr, date, time, train_type=tt_code,
                include_no_seats=include_no_seats, include_waiting_list=include_waiting_list,
            )
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
        except NoResultsError:
            raise NoResults(f"'{dep}'→'{arr}' 조회 결과가 없습니다")
        except KorailError as e:
            raise KorailClientError(f"Korail 오류: {e}") from e
        except Exception as e:
            raise NetworkError(f"네트워크 오류: {e}") from e

        results = []
        for t in trains:
            results.append(TrainInfo(
                train_type=t.train_type_name or "",
                train_no=t.train_no or "",
                dep_name=t.dep_name or "",
                arr_name=t.arr_name or "",
                dep_date=t.dep_date or "",
                dep_time=t.dep_time or "",
                arr_date=t.arr_date or "",
                arr_time=t.arr_time or "",
                general_available=t.has_general_seat() if hasattr(t, 'has_general_seat') else False,
                special_available=t.has_special_seat() if hasattr(t, 'has_special_seat') else False,
                waiting_possible=t.has_general_waiting_list() if hasattr(t, 'has_general_waiting_list') else False,
                _raw=t,
            ))
        if not results:
            raise NoResults(f"'{dep}'→'{arr}' 조건에 맞는 열차가 없습니다")
        return results

    def reserve(
        self, train: TrainInfo, seat_option: str = "general-first",
        try_waiting: bool = False,
    ) -> ReservationInfo:
        if not self._logged_in or self._korail is None:
            raise AuthError("로그인이 필요합니다")
        opt_map = {
            "general-first": ReserveOption.GENERAL_FIRST, "general-only": ReserveOption.GENERAL_ONLY,
            "special-first": ReserveOption.SPECIAL_FIRST, "special-only": ReserveOption.SPECIAL_ONLY,
        }
        option = opt_map.get(seat_option, ReserveOption.GENERAL_FIRST)
        try:
            rsv = self._korail.reserve(train._raw, option=option, try_waiting=try_waiting)
        except SoldOutError as e:
            raise SoldOut(f"매진: {e}") from e
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
        except KorailError as e:
            raise KorailClientError(f"예약 실패: {e}") from e
        except Exception as e:
            raise NetworkError(f"네트워크 오류: {e}") from e
        return ReservationInfo(
            rsv_id=rsv.rsv_id or "",
            train_type=rsv.train_type_name or "",
            train_no=rsv.train_no or "",
            dep_name=rsv.dep_name or "",
            arr_name=rsv.arr_name or "",
            dep_date=rsv.dep_date or "",
            dep_time=rsv.dep_time or "",
            arr_time=rsv.arr_time or "",
            price=rsv.price if hasattr(rsv, 'price') else 0,
            seat_count=rsv.seat_no_count if hasattr(rsv, 'seat_no_count') else 1,
            buy_limit_date=rsv.buy_limit_date if hasattr(rsv, 'buy_limit_date') else "",
            buy_limit_time=rsv.buy_limit_time if hasattr(rsv, 'buy_limit_time') else "",
            _raw=rsv,
        )

    def reservations(self) -> list[ReservationInfo]:
        if not self._logged_in or self._korail is None:
            raise AuthError("로그인이 필요합니다")
        try:
            rsv_list = self._korail.reservations()
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
        except KorailError as e:
            raise KorailClientError(f"예약 내역 조회 실패: {e}") from e
        except Exception as e:
            raise NetworkError(f"네트워크 오류: {e}") from e
        results = []
        for r in rsv_list:
            results.append(ReservationInfo(
                rsv_id=r.rsv_id or "",
                train_type=r.train_type_name or "",
                train_no=r.train_no or "",
                dep_name=r.dep_name or "",
                arr_name=r.arr_name or "",
                dep_date=r.dep_date or "",
                dep_time=r.dep_time or "",
                arr_time=r.arr_time or "",
                price=r.price if hasattr(r, 'price') else 0,
                seat_count=r.seat_no_count if hasattr(r, 'seat_no_count') else 1,
                buy_limit_date=r.buy_limit_date if hasattr(r, 'buy_limit_date') else "",
                buy_limit_time=r.buy_limit_time if hasattr(r, 'buy_limit_time') else "",
                _raw=r,
            ))
        return results

    def cancel(self, reservation: ReservationInfo) -> bool:
        if not self._logged_in or self._korail is None:
            raise AuthError("로그인이 필요합니다")
        try:
            return self._korail.cancel(reservation._raw)
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
        except KorailError as e:
            raise KorailClientError(f"취소 실패: {e}") from e
        except Exception as e:
            raise NetworkError(f"네트워크 오류: {e}") from e
