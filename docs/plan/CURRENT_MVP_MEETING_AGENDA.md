# AI Smart Factory Agent Office 현재 MVP 회의 안건

이 문서의 ‘현재 상태’와 미완료 항목은 회의 당시의 기록이다. 이후 2026년 10월 8일~12일 Google Forms 익명 유효 응답 6건을 수집했다([사용자 피드백 기록](../03_사용자_피드백_기록.md)). 식별정보를 수집하지 않아 응답 중복 여부와 고유 참여자 5명 이상 여부는 확인할 수 없다. **응답 6건**은 **참여자 6명** 또는 최소 5명 참여 완료를 뜻하지 않는다.

## 회의 목적

현재 구현된 MVP를 실제 팀 테스트와 대회 제출 단계로 넘기기 위해,
테스트 역할·RAG 교육 프로젝트·문서 언어·대회 참여 가능성·외부 배포 조건을 확정한다.

## 1. 현재 MVP 상태 공유

- Normal / Abnormal / HITL Workflow
- ML Random Forest 정상·손상 분류
- RAG 검색과 citation
- LangGraph Agent Workflow
- Long-term Memory
- Multimodal 이미지 관찰
- SSE와 Agent Office UI
- P0 버그 0
- 로컬 E2E 검증 완료

회의 당시 확인할 미완료 항목:

- 실제 사용자 5명 테스트
- 외부 배포와 Production smoke test
- 최종 README 빈칸
- 대회 참가 분야와 팀 자격 확인

## 2. 테스트 역할과 버그 리포트 방식

### 테스트 팀원

팀원들은 코드를 수정하지 않고 테스트와 버그 리포트만 작성한다.

| 역할 | 담당 |
|---|---|
| 실행·환경 담당 | 설치, 서버 실행, 접속, Health/Ready 확인 |
| 시나리오·기록 담당 | Normal/Abnormal/HITL 실행과 결과 기록 |
| 근거 검토 담당 | RAG 문서·출처·페이지 검증 |
| 사용자 경험 담당 | 화면 문구·상태·Report 이해도 검토 |

### 메인 개발자

- 버그 리포트 접수
- 원인 분석
- Codex를 통한 코드 수정
- 자동 테스트·회귀 테스트
- 수정 결과 공유
- 최종 배포

### 버그 리포트 필수 항목

```text
문제 제목
테스트 시나리오
선택한 Measurement
실행 단계
기대한 결과
실제 결과
오류 전문
스크린샷
재현 여부
긴급도(P0/P1/P2/P3)
```

## 3. RAG 미니프로젝트 운영

확정 자료:

- `docs/plan/RAG_MVP_ASSIGNMENTS.md` — 과제지
- `docs/plan/RAG_MVP_PROMPTS.md` — 한 번만 붙여 넣는 마스터 프롬프트

운영 방식:

```text
마스터 프롬프트 한 번 입력
→ ChatGPT/Claude가 과제 1부터 안내
→ 학습자가 직접 구현·실행
→ 결과 제출
→ YES면 다음 과제 / NO면 쉬운 재설명
```

확정할 사항:

- 사용할 ChatGPT 또는 Claude
- 실습 참가자
- 실습 시간
- Streamlit 화면까지 구현할지 여부
- 결과 제출 방식

## 4. 데이터셋과 RAG 문서 구성

### 현재 데이터셋

- Paderborn Measurement 원본: 영문 원본 파일
- 라벨: K001 정상, KA01·KI01 손상
- 현재 확보: 3개 archive, 240개 Measurement
- 전체 32개 archive 확보 상태는 아님

### 현재 RAG 문서

- Paderborn Overview
- Operating Conditions
- Bearing Damage
- Paderborn Benchmark Paper
- SKF Vibration Diagnostic Guide
- SKF Bearing Damage and Failure Analysis

### 결정할 사항

- 원문 영문을 그대로 사용할지
- 한글 요약본을 별도 문서로 만들지
- 원문과 한글 요약을 함께 검색할지
- 번역문을 공식 출처처럼 표시하지 않는 방법
- 번역·요약에 대한 검토 담당자
- 저작권 문서의 번역본 저장·배포 범위

## 5. 한글화 전략

권장안:

```text
원문 문서 보존
→ 팀 내부용 한글 요약·용어집 작성
→ 원문 source_id 연결
→ 화면 설명은 한글 중심
→ citation은 원문 문서명·페이지 유지
```

확인할 항목:

- Dataset 원문을 한국어로 번역해 공개해도 되는가
- SKF 문서 번역본을 Repository에 포함해도 되는가
- 한글 요약이 원문과 다를 때 누가 검토하는가
- 기술 용어 표준: RMS, Kurtosis, Crest Factor, Evidence 등

## 6. 영문 데이터·문서로 대회 참여가 가능한가

회의에서 먼저 구분한다.

### 대회 참여 가능성

영문 Dataset과 RAG 문서를 사용하는 것 자체가 곧 참여 불가 사유는 아니다.
다만 다음은 대회 운영진 공고와 제출 규정을 직접 확인해야 한다.

- Dataset 사용·출처 표기 조건
- 기술문서 저작권과 재배포 가능 여부
- 제출 화면의 한글 요구 여부
- 발표자료와 README의 언어 요구 여부
- 팀 인원 제한
- AI 도구 사용 고지 형식

### 현재 안전한 제출 방향

- 데이터·기술문서 원문은 영문 그대로 보존
- UI와 발표 설명은 한글 중심
- 핵심 영문 용어는 한글과 병기
- citation에는 원문 제목과 공식 출처 유지
- 번역·요약은 내부 보조자료로 명시
- 운영진에게 서면 확인 후 최종 제출

## 7. 외부 배포와 실제 사용자 테스트

### 회의 당시 상태

- 로컬 Health/Ready: 통과
- 로컬 Normal/Abnormal/HITL: 통과
- 외부 URL: 없음
- 실제 사용자 5명 테스트: 미실행

### 결정할 사항

- 외부 배포 플랫폼
- 공개 범위: 전체 공개 / 초대 사용자 / 비공개 시연
- Dataset·RAG 문서가 서버에 저장되는 방식
- 이미지 업로드 개인정보 처리
- 외부 배포 후 smoke test 담당자
- 실제 사용자 테스트 일정과 참가자 모집

## 8. 최종 README와 제출물 담당

담당자를 정해 아래 빈칸을 채운다.

- 팀원·역할
- 참가 분야
- 설치·실행 명령
- ML/RAG 평가 수치
- 사용자 테스트 결과
- 외부 배포 URL
- Sources/Licenses
- AI 활용 고지
- 한계와 향후 계획

## 9. 추가로 반드시 결정할 안건

### 데이터 운영 구조

- 원본 `.mat` 파일과 운영용 특징값 저장소를 분리할지
- Measurement Feature Catalog를 추가할지
- 학습용·평가용·운영용 데이터를 분리하는 방법

### 시연 시나리오

- 대표 Normal Measurement
- 대표 Abnormal Measurement
- HITL 경로
- RAG 근거 화면
- 최종 Report 화면
- 이미지 기능을 시연에 포함할지 여부

### 릴리스 기준

```text
P0 = 0
Normal E2E 통과
Abnormal E2E 통과
HITL 통과
Citation 통과
Ground Truth Leakage 통과
실제 사용자 테스트 완료
외부 배포 Smoke Test 통과
```

## 회의 종료 시 확정할 것

1. 테스트 참가자와 역할
2. 버그 리포트 전달 방식
3. 메인 개발자와 수정 승인자
4. RAG 미니프로젝트 시작일
5. 한글화 범위
6. 대회 운영진 확인 담당자
7. 외부 배포 플랫폼
8. 실제 사용자 테스트 일정
9. 최종 README 담당자
10. 최종 Release 승인 조건
