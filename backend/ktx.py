"""
ktx.py — korail2 기반 KTX 예매 래퍼 (Dynapath 대응 포함)
"""
import base64
import os
import random
import re
import string
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
except ImportError:
    AES = None
    pad = None

from korail2 import Korail, KorailError, NeedToLoginError, NoResultsError, SoldOutError
from korail2.korail2 import TrainType, ReserveOption


# ─── Dynapath Anti-bot 대응 ────────────────────────────

DEFAULT_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N Build/UP1A.231005.007)"

DYNAPATH_PATHS = [
    "/classes/com.korail.mobile.certification.TicketReservation",
    "/classes/com.korail.mobile.nonMember.NonMemTicket",
    "/classes/com.korail.mobile.research.TrainResearch",
    "/classes/com.korail.mobile.research.ResidualSeatsResearch.do",
    "/classes/com.korail.mobile.seatMovie.ScheduleView",
    "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial",
    "/classes/com.korail.mobile.trn.prcFare.do",
    "/classes/com.korail.mobile.login.Login",
]


class DynaPathMasterEngine:
    APP_ID = "com.korail.talk"
    AS_VALUE = "%5B38ff229cb34c7dda8e28220a2d750cce%5D"
    DEVICE_MODEL = "SM-S928N"
    OS_TYPE = "Android"
    SDK_VERSION = "v1"

    def __init__(self):
        self.table = "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"
        self.i8 = 161
        self.i9 = 30
        self.i10 = 2
        self.app_start_ts = str(int(time.time() * 1000))

    def string2xa1s(self, data):
        result = []
        idx = 0
        while idx < len(data):
            cp = ord(data[idx])
            idx += 1
            if cp < 128:
                result.append(cp)
            elif cp < 2048:
                result.append(128 | ((cp >> 7) & 15))
                result.append(cp & 127)
            elif cp >= 262144:
                result.append(160)
                result.append((cp >> 14) & 127)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
            elif (63488 & cp) != 55296:
                result.append(((cp >> 14) & 15) | 144)
                result.append((cp >> 7) & 127)
                result.append(cp & 127)
        return result

    def make_key(self, key):
        total = 0
        for ch in key:
            cp = ord(ch)
            bit = 32768
            for _ in range(16):
                if bit & cp:
                    break
                bit >>= 1
            total = (total * (bit << 1)) + cp
        return total

    def internal_char(self, base_table, remainder, current):
        seen = 0
        for ch in base_table:
            if ch in current:
                continue
            if seen == remainder:
                return ch
            seen += 1
        return " "

    def make_encode_table(self, number, encode_size, base_table):
        chars = ""
        temp = number
        for idx in range(encode_size):
            divisor = encode_size - idx
            remainder = temp % divisor
            chars += self.internal_char(base_table, remainder, chars)
            temp //= divisor
        return chars

    def encode_normal_be(self, data, table):
        values = self.string2xa1s(data)
        output = []
        digits = [0] * (self.i10 + 1)
        idx = 0
        tail = len(values) % self.i10
        body_size = len(values) - tail
        while idx < body_size:
            value = 0
            for _ in range(self.i10):
                value = (value * self.i8) + values[idx]
                idx += 1
            for di in range(self.i10 + 1):
                digits[di] = value % self.i9
                value //= self.i9
            for di in range(self.i10, -1, -1):
                output.append(table[digits[di]])
        if tail > 0:
            value = 0
            for _ in range(tail):
                value = (value * self.i8) + values[idx]
                idx += 1
            for di in range(tail + 1):
                digits[di] = value % self.i9
                value //= self.i9
            while tail >= 0:
                output.append(table[digits[tail]])
                tail -= 1
        return "".join(output)

    def generate_token(self, device_id, timestamp_ms, nonce):
        plaintext = (
            f"ai={self.APP_ID}&di={device_id}&as={self.AS_VALUE}&su=false&dbg=false&emu=false&hk=false"
            f"&it={self.app_start_ts}&ts={timestamp_ms}&rt=0&os=13&dm={self.DEVICE_MODEL}&st={self.OS_TYPE}&sv={self.SDK_VERSION}"
        )
        dyn_key = f"v1+{nonce}+{timestamp_ms}"
        key_encoded = self.encode_normal_be(dyn_key, self.table)
        table = self.make_encode_table(self.make_key(dyn_key), self.i9, self.table)
        body_encoded = self.encode_normal_be(plaintext, table)
        return f"bEeEP{self.table[len(key_encoded)]}{key_encoded}{body_encoded}"


# ─── korail2 패치 적용 ─────────────────────────────────

_original_request = None


def _patch_korail():
    """korail2 모듈 상수 + requests.Session 패치"""
    global _original_request
    import requests
    import korail2.korail2 as korail_mod

    # 버전/UA 패치 (생성 전에 적용)
    korail_mod.DEFAULT_USER_AGENT = DEFAULT_USER_AGENT
    korail_mod.KORAIL_DOMAIN = "https://smart.letskorail.com:443"

    engine = DynaPathMasterEngine()
    sid_key = b"2485dd54d9deaa36"
    device_id = "558a4f02041657ea"
    _device = "AD"

    original_send = requests.Session.send

    def patched_send(self, req, **kwargs):
        url = req.url
        if any(path in url for path in DYNAPATH_PATHS):
            # User-Agent
            req.headers["User-Agent"] = DEFAULT_USER_AGENT
            # Dynapath token
            ts = int(time.time() * 1000)
            nonce = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            req.headers["x-dynapath-m-token"] = engine.generate_token(device_id, ts, nonce)

            # Sid 파라미터 (POST=body, GET=query string)
            if AES is not None and pad is not None:
                plaintext = f"{_device}{ts}".encode("utf-8")
                cipher = AES.new(sid_key, AES.MODE_CBC, iv=sid_key)
                sid = base64.b64encode(cipher.encrypt(pad(plaintext, 16))).decode("utf-8") + "\n"

                if req.method == "GET":
                    separator = "&" if "?" in req.url else "?"
                    req.url = req.url + separator + f"Sid={sid}"
                elif req.body:
                    body = req.body
                    if isinstance(body, bytes):
                        body = body.decode("utf-8", errors="replace")
                    if "Sid=" not in body:
                        req.body = body + ("" if body.endswith("&") else "&") + f"Sid={sid}"
        return original_send(self, req, **kwargs)

    requests.Session.send = patched_send
    _original_request = original_send


_patch_korail()


# ─── 도메인 데이터 클래스 ───────────────────────────────


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
    def dep_display(self):
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self):
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def duration(self):
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
    def dep_display(self):
        return f"{self.dep_time[:2]}:{self.dep_time[2:4]}"

    @property
    def arr_display(self):
        return f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

    @property
    def limit_display(self):
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
        self._korail = None
        self._logged_in = False
        self._user_name = ""

    @property
    def logged_in(self):
        return self._logged_in and self._korail is not None

    @property
    def user_name(self):
        return self._user_name

    def login(self, korail_id, korail_pw):
        import requests
        try:
            self._korail = Korail(korail_id, korail_pw, auto_login=True)

            # korail2.login()은 실패 시 False 반환 (예외 미발생)
            if not hasattr(self._korail, 'logined') or not self._korail.logined:
                self._logged_in = False
                self._korail = None
                raise AuthError("로그인 실패: Korail 계정 정보를 확인해주세요")

            self._logged_in = True
            self._user_name = getattr(self._korail, 'name', '') or ''
            return self._user_name
        except AuthError:
            raise
        except NeedToLoginError as e:
            self._logged_in = False
            raise AuthError(f"로그인 실패: {e}") from e
        except KorailError as e:
            self._logged_in = False
            msg = str(e)
            if "MACRO" in msg:
                raise AuthError(f"Korail 매크로 감지: {msg}") from e
            raise AuthError(f"Korail 오류: {msg}") from e
        except Exception as e:
            self._logged_in = False
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"네트워크 연결 실패: {e}") from e
            raise KorailClientError(f"알 수 없는 오류: {e}") from e

    def search(self, dep, arr, date=None, time=None, train_type="ktx",
               include_no_seats=False, include_waiting_list=False):
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

    def reserve(self, train, seat_option="general-first", try_waiting=False):
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
            rsv_id=rsv.rsv_id or "", train_type=rsv.train_type_name or "",
            train_no=rsv.train_no or "", dep_name=rsv.dep_name or "",
            arr_name=rsv.arr_name or "", dep_date=rsv.dep_date or "",
            dep_time=rsv.dep_time or "", arr_time=rsv.arr_time or "",
            price=rsv.price if hasattr(rsv, 'price') else 0,
            seat_count=rsv.seat_no_count if hasattr(rsv, 'seat_no_count') else 1,
            buy_limit_date=rsv.buy_limit_date if hasattr(rsv, 'buy_limit_date') else "",
            buy_limit_time=rsv.buy_limit_time if hasattr(rsv, 'buy_limit_time') else "",
            _raw=rsv,
        )

    def reservations(self):
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
                rsv_id=r.rsv_id or "", train_type=r.train_type_name or "",
                train_no=r.train_no or "", dep_name=r.dep_name or "",
                arr_name=r.arr_name or "", dep_date=r.dep_date or "",
                dep_time=r.dep_time or "", arr_time=r.arr_time or "",
                price=r.price if hasattr(r, 'price') else 0,
                seat_count=r.seat_no_count if hasattr(r, 'seat_no_count') else 1,
                buy_limit_date=r.buy_limit_date if hasattr(r, 'buy_limit_date') else "",
                buy_limit_time=r.buy_limit_time if hasattr(r, 'buy_limit_time') else "",
                _raw=r,
            ))
        return results

    def cancel(self, reservation):
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
