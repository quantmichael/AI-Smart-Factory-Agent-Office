# RAG MVP 미니프로젝트 과제지

이 문서는 학습자가 순서대로 수행할 과제만 담고 있다. 처음에는
[RAG_MVP_PROMPTS.md](./RAG_MVP_PROMPTS.md)의 마스터 프롬프트를 한 번만 붙여 넣고,
ChatGPT/Claude 튜터가 과제 1부터 순서대로 안내하도록 한다.

## 진행 방식

```text
마스터 프롬프트 한 번 입력 → 과제 안내 받기 → 직접 구현·실행 → YES/NO 응답 → 통과 후 다음 과제
```

학습자가 파일 작성과 실행을 직접 수행한다.

## 사용할 참고 설계 문서

- `docs/plan/04_RAG_DESIGN.md`
- `docs/plan/07_API_DB_SPEC.md`의 Knowledge Base API와 EvidenceObject 부분
- `docs/plan/08_EVALUATION_TEST_PLAN.md`의 RAG 평가 부분
- `README.md`의 RAG ingestion/search 부분

## 실제 RAG 문서

처음에는 아래 3개만 사용한다.

| source_id | 제목 | 위치 |
|---|---|---|
| `PADERBORN_OVERVIEW` | Bearing DataCenter overview | `knowledge/bearing_v1/paderborn/bearing_datacenter_overview.html` |
| `PADERBORN_OPERATING_CONDITIONS` | Operating Conditions | `knowledge/bearing_v1/paderborn/operating_conditions.html` |
| `PADERBORN_DAMAGE` | Bearing Damage | `knowledge/bearing_v1/paderborn/bearing_damage.html` |

확장 단계에서 다음 문서를 추가한다.

- `PADERBORN_BENCHMARK_PAPER`
- `SKF_VIBRATION_DIAGNOSTIC_GUIDE`
- `SKF_BEARING_DAMAGE_FAILURE_ANALYSIS`

Paderborn 원본 RAR과 Ground Truth 전용 문서는 첫 runtime 검색에서 제외한다.
SKF 자료는 로컬 학습용으로만 사용하고 재배포하지 않는다.

## 필요한 라이브러리

`chromadb`, `scikit-learn`, `numpy`, `pypdf`, `beautifulsoup4`, `fastapi`, `uvicorn`, `streamlit`, `pytest`.
ChatGPT/Claude에게 Prompt P00으로 `requirements-mini.txt`를 만들게 한 뒤 직접 설치한다.

## 과제 목록

### 과제 1 — RAG 전체 흐름 이해

Knowledge Pack, Manifest, Document, Chunk, Embedding, Vector Store, Retrieval,
EvidenceObject, Citation의 뜻과 관계를 그림으로 정리한다.

제출물: 용어표와 `문서 → 조각 → 벡터 → 저장 → 검색 → 근거` 흐름.

사용 프롬프트: `P01`

### 과제 2 — 독립 프로젝트 구조

다음 폴더를 직접 만든다.

```text
rag-mini-project/
├── knowledge/
├── app/
├── tests/
├── evaluation/
├── artifacts/
└── README.md
```

사용 프롬프트: `P02`

### 과제 3 — 문서와 출처 목록

최소 3개 문서와 `knowledge/manifest.json`을 만든다.
`source_id`, 제목, 출처, 버전, 라이선스, 파일 경로를 기록한다.

사용 프롬프트: `P03`

### 과제 4 — 문서 읽기와 조각 만들기

TXT/HTML/PDF를 읽고 `chunk_id`, `content`, `source_id`, `title`, `page`, `section`을 가진 조각을 만든다.
동일 입력에서 동일한 ID가 나오도록 한다.

사용 프롬프트: `P04`

### 과제 5 — 로컬 임베딩과 Chroma 저장

외부 API 없이 문서 조각을 벡터화하고 `bearing_v1` 컬렉션에 저장한다.
같은 문서를 다시 넣었을 때 중복되지 않아야 한다.

사용 프롬프트: `P05`

### 과제 6 — 목적별 검색

`DATASET_EVIDENCE`, `DIAGNOSTIC_EVIDENCE`, `INSPECTION_ACTION` 목적을 지원한다.
검색 결과는 본문과 출처를 함께 반환한다.

사용 프롬프트: `P06`

### 과제 7 — EvidenceObject와 근거 상태

`content`와 출처 정보를 가진 EvidenceObject를 만들고,
`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`을 판정한다.

사용 프롬프트: `P07`

### 과제 8 — FastAPI 검색 API

`POST /knowledge/search`를 구현한다. 요청에는 query, purpose, top_k, filters를 사용한다.

사용 프롬프트: `P08`

### 과제 9 — RAG 평가

진단·손상·점검·운전 조건·답변 불가·충돌 질문을 포함한 20개 평가 질문을 만든다.
Hit@3, Hit@5, Recall@5, MRR, Expected Source Hit Rate, Empty Result Rate를 계산한다.

사용 프롬프트: `P09`

### 과제 10 — 오류 수정과 전체 재시험

문제 발생 시 오류 전문을 튜터에게 제출하고, 수정 후 기존 테스트까지 다시 실행한다.

사용 프롬프트: `P10`

### 과제 11 — Streamlit 검색 화면

질문 입력, 검색 목적 선택, 검색 결과, 문서 본문, 출처, 근거 부족 안내를 표시한다.

```bash
streamlit run streamlit_app.py --server.port 8501
```

브라우저: `http://127.0.0.1:8501`

사용 프롬프트: `P11`

### 과제 12 — 최종 브라우저 시험

정상 질문, 손상 질문, 점검 질문, 문서에 없는 질문, 목적 변경, 서버 중지 상황을 시험한다.

사용 프롬프트: `P12`

## 최종 제출물

- `README.md`
- `knowledge/manifest.json`
- 문서 로더·조각 생성기
- 로컬 임베딩·Chroma 저장 코드
- 목적별 검색 코드
- EvidenceObject·근거 상태 검사
- FastAPI 검색 API
- Streamlit 화면
- 20개 이상 평가 질문과 지표
- 테스트 결과와 개선 기록

## 완료 기준

- [ ] 문서와 출처가 추적됨
- [ ] 중복 저장이 방지됨
- [ ] 검색 결과에 `content`와 출처가 있음
- [ ] 근거 부족·충돌 상태가 있음
- [ ] API와 Streamlit 화면이 동작함
- [ ] 평가 지표가 생성됨
- [ ] pytest가 통과함
