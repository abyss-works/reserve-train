# reserve-train — KTX 예매 앱

> board/used-book 패턴 계승: Vue 3 + FastAPI, 단일 컨테이너

## 프로젝트 구조

```
reserve-train/
├── backend/
│   ├── main.py          # FastAPI 앱 + 정적파일 서빙
│   ├── api.py           # REST 엔드포인트 (/api/*)
│   ├── ktx.py           # korail2 래퍼
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/         # API 호출 (fetch)
│       ├── stores/      # Pinia stores
│       ├── views/       # LoginView, SearchView, ReservationsView
│       ├── components/  # NavBar, TrainCard
│       ├── router/      # Vue Router
│       └── types/       # TypeScript 타입
├── k8s/prod/            # Kustomize manifests
├── Dockerfile           # 멀티스테이지 (node → python)
└── AGENTS.md
```

## API

| Method | Path | 설명 |
|--------|------|------|
| POST | /api/v1/login | Korail 로그인 |
| GET | /api/v1/search | 열차 조회 |
| POST | /api/v1/reserve | 예약 |
| GET | /api/v1/reservations | 예약 내역 |
| POST | /api/v1/cancel | 취소 |
| POST | /api/v1/logout | 로그아웃 |

## 배포

```bash
docker build -t registry.abyssworks.dev/reserve-train:prod .
docker push registry.abyssworks.dev/reserve-train:prod
kubectl kustomize k8s/prod/ | kubectl apply -f -
```
