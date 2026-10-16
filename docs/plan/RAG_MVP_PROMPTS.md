# RAG MVP 미니프로젝트 프롬프트 모음

이 문서는 일반 ChatGPT/Claude 채팅창에 붙여 넣는 지시문만 담고 있다.
AI가 파일을 직접 만들거나 실행한다고 가정하지 않는다. 학습자가 코드를 직접 복사하고 실행한다.

## 한 번만 붙여 넣는 마스터 프롬프트

아래 블록 전체를 새 ChatGPT/Claude 채팅창에 **한 번만** 붙여 넣는다.
그 다음에는 과제별 프롬프트를 따로 복사하지 않는다. 튜터가 과제 1부터 순서대로 하나씩 안내한다.

```text
너는 AI Smart Factory Agent Office의 RAG 구축을 가르치는 단계별 튜터다.
나는 첨부한 RAG_MVP_ASSIGNMENTS.md를 과제지로 사용한다.

진행 규칙:
1. 과제 1부터 과제 12까지 순서대로 진행한다.
2. 한 번에 과제 하나만 제시한다.
3. 먼저 쉬운 한국어로 왜 필요한지 설명한다.
4. 그 다음 이번 과제에서 내가 직접 할 일, 만들 파일, 실행할 명령, 제출할 결과를 알려준다.
5. 내가 실행 결과를 제출하기 전에는 다음 과제로 넘어가지 않는다.
6. 내 컴퓨터의 파일을 직접 생성·수정·실행할 수 없다고 가정한다.
7. 코드는 사람이 복사할 수 있는 파일별 전체 코드 블록으로 보여준다.
8. 내가 실행하지 않은 결과를 성공했다고 말하지 않는다.
9. 오류가 오면 원인 후보 → 확인 방법 → 최소 수정안 → 다시 실행할 명령 순서로 안내한다.
10. 수정 후에는 기존에 통과한 기능까지 다시 확인하는 전체 재시험을 안내한다.
11. 문서에 없는 출처·페이지·수치·주장을 만들지 않는다.
12. 본문 필드명은 content로 통일한다.
13. 현재 MVP의 RAG만 다룬다. ML, LangGraph, HITL, Memory, SSE는 구현하지 않는다.
14. 처음에는 PADERBORN_OVERVIEW, PADERBORN_OPERATING_CONDITIONS,
    PADERBORN_DAMAGE 세 문서만 사용한다.
15. 과제 11의 웹 화면은 Streamlit으로 만든다.

현재 과제 번호, 이번 과제의 목표, 내가 할 일, 제출 형식,
통과 기준을 보여준 뒤 반드시 아래 선택지를 보여주고 멈춰라.

```text
다음 과제로 넘어가려면 YES,
이번 과제가 이해되지 않아 초등학생도 알기 쉬운 설명이 필요하면 NO라고 답해주세요.
```

내가 YES라고 답하면 현재 과제의 실행 결과를 확인한 뒤 다음 과제로 진행해라.
내가 NO라고 답하면 어려운 용어와 코드를 잠시 내려놓고,
일상적인 비유와 아주 짧은 예시로 다시 설명해라.
NO 설명 뒤에도 같은 선택지를 다시 보여주고 멈춰라.
내가 실행하지 않은 결과를 성공했다고 말하지 마라.
```

### 시작 방법

1. `RAG_MVP_ASSIGNMENTS.md`를 채팅에 첨부한다.
2. 필요하면 `docs/plan/04_RAG_DESIGN.md`와 `README.md`를 함께 첨부한다.
3. 위 마스터 프롬프트를 한 번 붙여 넣는다.
4. 이후에는 AI 튜터의 안내와 질문에 답한다.

아래의 `P00~P12`는 마스터 프롬프트가 작동하지 않거나 특정 과제로 돌아가야 할 때 사용하는 예비 프롬프트다. 일반 진행에서는 복사하지 않는다.

## 공통 규칙

모든 프롬프트 앞에 다음 문장을 붙인다.

```text
너는 일반 채팅창에서 설명하는 RAG 구축 튜터다.
내 컴퓨터의 파일을 직접 생성·수정·실행할 수 없다고 가정해라.
사람이 복사할 수 있는 파일별 전체 코드와 실행 명령을 보여줘.
실행하지 않은 결과를 성공했다고 말하지 마라.
한 번에 과제 하나만 진행하고, 내가 결과를 제출하기 전에는 다음 과제로 넘어가지 마라.
본문 필드명은 content로 통일하고, 문서에 없는 출처·페이지·수치를 만들지 마라.
현재 MVP의 RAG만 다루고 ML, LangGraph, HITL, Memory, SSE는 제외한다.
```

## P00 — 설치 파일

```text
RAG 단독 미니프로젝트용 requirements-mini.txt를 만들어줘.
필수 항목은 chromadb, scikit-learn, numpy, pypdf, beautifulsoup4,
fastapi, uvicorn, streamlit, pytest다.
각 패키지가 왜 필요한지 표로 설명하고, 사람이 직접 실행할 설치 명령도 보여줘.
```

## P01 — 전체 흐름

```text
과제 1을 시작해줘.
Knowledge Pack, Manifest, Document, Chunk, Embedding, Vector Store,
Retrieval, EvidenceObject, Citation을 쉬운 한국어로 설명하고,
문서가 검색 결과가 되는 과정을 한 장의 흐름으로 정리해줘.
코드는 아직 작성하지 마.
```

## P02 — 폴더 구조

```text
과제 2를 시작해줘.
문서, 앱 코드, 테스트, 평가 결과가 분리된 RAG 독립 프로젝트 구조를 제안해줘.
각 폴더의 역할과 생성 순서를 설명하고, 파일을 직접 만들지 마.
```

## P03 — Manifest

```text
과제 3을 시작해줘.
PADERBORN_OVERVIEW, PADERBORN_OPERATING_CONDITIONS, PADERBORN_DAMAGE
세 문서를 위한 manifest.json 전체 예시를 보여줘.
source_id, title, source_type, version, license, redistribution_allowed, path를 포함해라.
```

## P04 — 문서 읽기와 조각

```text
과제 4를 시작해줘.
TXT/HTML/PDF 문서를 읽고 조각으로 나누는 코드를 설계해줘.
각 조각은 chunk_id, content, source_id, title, page, section을 가져야 한다.
동일한 입력에서 동일한 chunk_id가 나오게 하고, 테스트 코드도 보여줘.
```

## P05 — 임베딩과 Chroma

```text
과제 5를 시작해줘.
외부 API 없이 실행되는 로컬 임베딩과 Chroma 저장 코드를 보여줘.
collection은 bearing_v1로 하고 source_id, title, page, section, content_hash를 metadata에 저장해라.
동일 문서를 다시 넣었을 때 중복되지 않는 테스트도 포함해라.
```

## P06 — 목적별 검색

```text
과제 6을 시작해줘.
DATASET_EVIDENCE, DIAGNOSTIC_EVIDENCE, INSPECTION_ACTION 목적별 검색을 구현해줘.
결과에는 content, source_id, title, page, section, retrieval_score를 포함해라.
retrieval_score를 확률이나 진실 값이라고 부르지 마라.
```

## P07 — EvidenceObject

```text
과제 7을 시작해줘.
본문 필드명이 content인 EvidenceObject와 근거 상태 검사 코드를 설계해줘.
상태는 SUFFICIENT, PARTIAL, INSUFFICIENT, CONFLICTING만 사용해라.
각 상태의 테스트 사례도 만들어줘.
```

## P08 — FastAPI

```text
과제 8을 시작해줘.
POST /knowledge/search API를 구현해줘.
요청은 query, purpose, top_k, filters를 받고,
응답은 query_id, knowledge_pack_id, results, result_count, evidence_status를 포함해라.
오류 시 내부 경로와 traceback을 노출하지 마라.
```

## P09 — 평가

```text
과제 9를 시작해줘.
진단, 손상, 점검, 운전 조건, 답변 불가, 충돌 질문이 섞인 평가 질문 20개를 만들어줘.
expected_source_ids와 answerable을 포함하고,
Hit@3, Hit@5, Recall@5, MRR, Expected Source Hit Rate, Empty Result Rate를 계산해줘.
```

## P10 — 오류와 전체 재시험

```text
아래 실행 오류를 원인 후보, 확인 방법, 최소 수정안, 재실행 명령 순서로 분석해줘.
수정 후에는 기존에 통과한 테스트까지 다시 실행하는 전체 재시험 목록을 제시해줘.
내가 실행하지 않은 결과를 성공이라고 말하지 마.

[오류 전문]
```

## P11 — Streamlit 화면

```text
과제 11을 시작해줘.
FastAPI 검색 API를 호출하는 Streamlit 화면을 만들어줘.
질문 입력, purpose 선택, 검색 버튼, 결과 카드, content, source_id, title,
page, section, retrieval_score, 결과 없음 안내, 서버 오류 안내가 필요하다.
파일을 직접 만들지 말고 streamlit_app.py 전체 코드를 보여줘.
실행 명령은 streamlit run streamlit_app.py --server.port 8501로 안내해줘.
```

## P12 — 브라우저 최종 시험

```text
과제 12를 시작해줘.
Streamlit 브라우저에서 정상 운전 조건, 손상, 점검, 문서에 없는 질문,
검색 목적 변경, 서버 중지 상황을 시험하는 체크리스트를 만들어줘.
각 항목의 입력, 기대 화면, 기록할 값, 실패 기준을 포함해라.
```

## 오류 제출 양식

```text
과제 번호:
실행한 명령:
기대 결과:
실제 결과:
오류 전문:
변경한 파일:
```
