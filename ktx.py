"""
ktx.py — korail2 기반 KTX 예매 래퍼

Streamlit(korail2.Korail)의 공식 API를 래핑하여
로그인/조회/예약/취소 기능을 제공한다.

Usage:
    from ktx import KorailClient

    client = KorailClient()
    client.login("id", "pw")
    trains = client.search("서울", "부산", "20260720", "090000")
    reservation = client.reserve(trains[0])
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from korail2 import Korail, KorailError, NeedToLoginError, NoResultsError, SoldOutError
from korail2.korail2 import Train as _Train, Reservation as _Reservation, TrainType, ReserveOption


# ─── 도메인 데이터 클래스 ───────────────────────────────────


@dataclass
class TrainInfo:
    """열차 정보 (korail2.Train 래핑)"""
    train_type: str          # KTX, ITX-청춘 등
    train_no: str            # 열차 번호
    dep_name: str            # 출발역
    arr_name: str            # 도착역
    dep_date: str            # 출발일 (YYYYMMDD)
    dep_time: str            # 출발시각 (HHMMSS)
    arr_date: str            # 도착일
    arr_time: str            # 도착시각 (HHMMSS)
    general_available: bool  # 일반실 예약 가능 여부
    special_available: bool  # 특실 예약 가능 여부
    waiting_possible: bool   # 예약 대기 가능 여부
    _raw: object = field(repr=False)

    @property
    def dep_display(self) -> str:
        """출발 시각 hh:mm"""
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self) -> str:
        """도착 시각 hh:mm"""
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def duration(self) -> str:
        """소요 시간"""
        h = int(self.arr_time[:2]) - int(self.dep_time[:2])
        m = int(self.arr_time[2:4]) - int(self.dep_time[2:4])
        if m < 0:
            h -= 1
            m += 60
        return f"{h}시간 {m}분"

    def __repr__(self) -> str:
        seats = []
        if self.general_available:
            seats.append("일반실 가능")
        elif self.waiting_possible:
            seats.append("예약대기")
        else:
            seats.append("일반실 매진")
        if self.special_available:
            seats.append("특실 가능")

        return (
            f"[{self.train_type} {self.train_no}] "
            f"{self.dep_name}({self.dep_display}) → "
            f"{self.arr_name}({self.arr_display}) "
            f"[{', '.join(seats)}]"
        )


@dataclass
class ReservationInfo:
    """예약 정보"""
    rsv_id: str              # 예약번호 (h_pnr_no)
    train_type: str
    train_no: str
    dep_name: str
    arr_name: str
    dep_date: str
    dep_time: str
    arr_time: str
    price: int               # 운임 (원)
    seat_count: int          # 좌석 수
    buy_limit_date: str      # 구입기한일 (YYYYMMDD)
    buy_limit_time: str      # 구입기한시각 (HHMMSS)
    _raw: object = field(repr=False)

    @property
    def dep_display(self) -> str:
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self) -> str:
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def limit_display(self) -> str:
        """구입기한 표시"""
        m = int(self.buy_limit_date[4:6])
        d = int(self.buy_limit_date[6:])
        t = f"{self.buy_limit_time[:2]}:{self.buy_limit_time[2:4]}"
        return f"{m}월 {d}일 {t}"

    def __repr__(self) -> str:
        return (
            f"[{self.train_type} {self.train_no}] "
            f"{self.dep_name}({self.dep_display}) → "
            f"{self.arr_name}({self.arr_display}) "
            f"{self.price:,}원({self.seat_count}석), "
            f"구입기한 {self.limit_display}"
        )


# ─── 사용자 정의 예외 ────────────────────────────────────


class KorailClientError(Exception):
    """기본 예외"""
    pass

class AuthError(KorailClientError):
    """로그인 실패"""
    pass

class NoResults(KorailClientError):
    """조회 결과 없음"""
    pass

class SoldOut(KorailClientError):
    """매진"""
    pass

class NetworkError(KorailClientError):
    """네트워크 오류"""
    pass


# ─── 메인 클라이언트 ─────────────────────────────────────


class KorailClient:
    """korail2 기반 KTX 예매 클라이언트

    사용법:
        client = KorailClient()
        client.login("010-1234-5678", "password")
        trains = client.search("서울", "부산", "20260720", "090000")
        rsv = client.reserve(trains[0])
        client.reservations()
        client.cancel(rsv)
    """

    def __init__(self):
        self._korail: Optional[Korail] = None
        self._logged_in: bool = False

    # ─── 로그인 ───────────────────────────────────────

    @property
    def logged_in(self) -> bool:
        return self._logged_in and self._korail is not None

    @property
    def user_name(self) -> Optional[str]:
        """로그인된 사용자 이름"""
        if self._korail and hasattr(self._korail, 'user_name'):
            return self._korail.user_name
        return None

    def login(self, korail_id: str, korail_pw: str) -> bool:
        """Korail 로그인

        Args:
            korail_id: 회원번호 / 이메일 / 전화번호
            korail_pw: 비밀번호

        Returns:
            True (성공 시)

        Raises:
            AuthError: 로그인 실패 (ID/PW 오류)
            NetworkError: 네트워크 연결 실패
        """
        try:
            self._korail = Korail(korail_id, korail_pw, auto_login=True)
            self._logged_in = True
            return True
        except NeedToLoginError as e:
            # Korail() 생성자에서 이미 로그인 시도, 실패 시 이 예외
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

    def _ensure_login(self):
        """로그인 상태 확인"""
        if not self._logged_in or self._korail is None:
            raise AuthError("로그인이 필요합니다")

    # ─── 열차 조회 ─────────────────────────────────────

    def search(
        self,
        dep: str,
        arr: str,
        date: Optional[str] = None,
        time: Optional[str] = None,
        train_type: str = "ktx",
        passengers: int = 1,
        include_no_seats: bool = False,
        include_waiting_list: bool = False,
    ) -> list[TrainInfo]:
        """열차 조회

        Args:
            dep: 출발역 (예: "서울")
            arr: 도착역 (예: "부산")
            date: 출발일 "YYYYMMDD" (기본: 오늘)
            time: 출발시각 "HHMMSS" 이후 검색 (기본: 첫차)
            train_type: 열차 종류 (ktx, itx-cheongchun, mugunghwa, all)
            passengers: 성인 인원 수 (기본: 1)
            include_no_seats: 좌석 없는 열차도 포함
            include_waiting_list: 예약대기 가능 열차도 포함

        Returns:
            TrainInfo 리스트

        Raises:
            AuthError: 로그인 필요
            NoResults: 조회 결과 없음
            NetworkError: 네트워크 오류
        """
        self._ensure_login()

        # train_type 매핑
        tt_map = {
            "ktx": TrainType.KTX,
            "ktx-sancheon": TrainType.KTX_SANCHEON,
            "itx-saemaeul": TrainType.ITX_SAEMAEUL,
            "itx-cheongchun": TrainType.ITX_CHEONGCHUN,
            "saemaeul": TrainType.SAEMAEUL,
            "mugunghwa": TrainType.MUGUNGHWA,
            "nuriro": TrainType.NURIRO,
            "airport": TrainType.AIRPORT,
            "all": TrainType.ALL,
        }
        tt_code = tt_map.get(train_type.lower(), TrainType.KTX)

        # 날짜 기본값: 오늘
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        if not time:
            time = "000000"

        try:
            trains = self._korail.search_train(
                dep, arr, date, time,
                train_type=tt_code,
                include_no_seats=include_no_seats,
                include_waiting_list=include_waiting_list,
            )
        except NoResultsError as e:
            raise NoResults(f"'{dep}'→'{arr}' 조회 결과가 없습니다") from e
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
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

    # ─── 예약 ──────────────────────────────────────────

    def reserve(
        self,
        train: TrainInfo,
        seat_option: str = "general-first",
        passengers: int = 1,
        try_waiting: bool = False,
    ) -> ReservationInfo:
        """열차 예약

        Args:
            train: TrainInfo 객체 (search 결과)
            seat_option: 좌석 옵션
                general-first (일반실 우선), general-only (일반실만),
                special-first (특실 우선), special-only (특실만)
            passengers: 성인 인원 수
            try_waiting: 매진 시 예약대기 시도 여부

        Returns:
            ReservationInfo

        Raises:
            AuthError: 로그인 필요
            SoldOut: 매진
        """
        self._ensure_login()

        opt_map = {
            "general-first": ReserveOption.GENERAL_FIRST,
            "general-only": ReserveOption.GENERAL_ONLY,
            "special-first": ReserveOption.SPECIAL_FIRST,
            "special-only": ReserveOption.SPECIAL_ONLY,
        }
        option = opt_map.get(seat_option, ReserveOption.GENERAL_FIRST)

        try:
            rsv = self._korail.reserve(
                train._raw,
                option=option,
                try_waiting=try_waiting,
            )
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

    # ─── 예약 내역 ────────────────────────────────────

    def reservations(self) -> list[ReservationInfo]:
        """내 예약 내역 조회

        Returns:
            ReservationInfo 리스트
        """
        self._ensure_login()

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

    # ─── 예약 취소 ─────────────────────────────────────

    def cancel(self, reservation: ReservationInfo) -> bool:
        """예약 취소

        Args:
            reservation: ReservationInfo 객체

        Returns:
            True (성공 시)
        """
        self._ensure_login()

        try:
            return self._korail.cancel(reservation._raw)
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError("로그인 세션 만료") from e
        except KorailError as e:
            raise KorailClientError(f"취소 실패: {e}") from e
        except Exception as e:
            raise NetworkError(f"네트워크 오류: {e}") from e
