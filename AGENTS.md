# AGENTS.md — reserve-train 프로젝트

> 이 문서는 reserve-train 프로젝트의 기술 스택, 구조, 컨벤션을 정의한다.

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 저장소 | `abyss-works/reserve-train` |
| 언어 | Python 3.11 |
| UI | Streamlit |
| 외부 API | Korail 모바일 API (smart.letskorail.com) via korail2 |
| 배포 | Docker → K3s 클러스터 |

## 로컬 저장소 경로

```
~/abyss-works/reserve-train/
```

## 디렉토리 구조

```
reserve-train/
├── app.py              # Streamlit 메인 앱
├── ktx.py              # korail2 래퍼
├── requirements.txt    # Python 의존성
├── Dockerfile          # 멀티스테이지 빌드
├── k8s/prod/           # Kustomize 기반 k8s manifests
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── AGENTS.md           # (이 파일)
└── README.md
```

## 빌드 & 배포

```bash
# 로컬 실행
pip install -r requirements.txt
streamlit run app.py

# Docker 빌드
docker build -t registry.abyssworks.dev/reserve-train:prod .
docker push registry.abyssworks.dev/reserve-train:prod

# K8s 배포
kustomize build k8s/prod/ | kubectl apply -f -
```

## 배포 (k8s)

- K3s 클러스터 (abyssworks)
- 네임스페이스: `reserve-train-prod`
- Ingress: `reserve-train.abyssworks.dev`
- TLS: *.abyssworks.dev wildcard cert (ingress-nginx)

## Credential

- KORAIL_ID, KORAIL_PW 환경변수 (K8s Secret)
- 로컬 개발 시 `.env` 파일 또는 Streamlit 로그인 폼
