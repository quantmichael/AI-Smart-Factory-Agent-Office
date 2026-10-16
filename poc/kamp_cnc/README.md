# KAMP CNC 확장 PoC

## 목적

이 개념 증명(Proof of Concept)은 KAMP CNC 제조 데이터와 공식 가이드북을 사용하여 Data Adapter 및 Knowledge/RAG 계층의 도메인 확장 가능성을 검증합니다. 기존 Paderborn Production E2E 애플리케이션과 완전히 분리되어 있습니다.

이 PoC는 Production Backend, Frontend, 데이터베이스, Checkpoint, Memory, Artifact, ML 모델, `bearing_v1`, Chroma 또는 배포 설정을 변경하거나 가져오거나 기록하지 않습니다.

## 검증 결과

| 검증 항목 | 결과 |
|---|---:|
| 데이터셋 | 1,085행 / 43열 |
| PASS | 986 |
| FAIL | 99 |
| Adapter 변환 | 1,085 / 1,085 |
| Feature 불일치 | 0 |
| 검증 실패 | 0 |
| Adapter + RAG 테스트 | 29 / 29 통과 |
| Knowledge Pack | `kamp_cnc_v1` |
| Knowledge chunk | 49 |
| FAIL Observation 검색 | 3 / 3 |
| 답변 보류 검증 | 3 / 3 |
| Production 변경 | 0 |
| Production DB 기록 | 0 |
| Production Chroma 기록 | 0 |

### 검증 산출물

상세 감사 및 검증 결과는 다음 문서에서 확인할 수 있습니다.

- [데이터셋 감사 결과](results/dataset_audit.md)
  - 데이터 구조, PASS/FAIL 분포, SerialNo 중복, Guidebook 교차검증, Leakage 위험 분석

- [Paired Serial Observation 감사 결과](results/paired_serial_audit.md)
  - 동일 SerialNo·동일 timestamp의 99개 PASS/FAIL 쌍에 대한 Feature 차이 분석

- [CNC Adapter 호환성 검증](results/compatibility_report.md)
  - 1,085개 Observation 변환, Ground Truth/Feature 보존 및 Adapter 호환성 검증

- [KAMP Guidebook RAG Evidence 검증](results/rag_evidence_report.md)
  - FAIL Observation 검색, 페이지·Section Evidence 추적 및 Abstention 검증

## 흐름

```text
KAMP CNC Data
    -> KAMPCNCAdapter
    -> Ground Truth Context
    -> kamp_cnc_v1 RAG
    -> Evidence / Abstention
```

## 정답값(Ground Truth) 및 주장 범위

- `passorfail`은 KAMP Dataset Ground Truth입니다.
- `passorfail=0`은 PASS / 양품을 의미합니다.
- `passorfail=1`은 FAIL / 불량을 의미합니다.
- Label 매핑: `0 = PASS`, `1 = FAIL`.
- 이 PoC의 CNC 상태는 ML prediction이 아닙니다.
- CNC ML 학습 및 accuracy/F1 평가는 수행하지 않았습니다.
- 이 PoC는 현장 일반화 성능을 주장하지 않습니다.
- Sensor Feature만으로 특정 고장 원인을 확정하지 않습니다.
- 유일한 RAG Knowledge Source는 이 데이터셋의 공식 KAMP Guidebook입니다.
- 이 PoC는 Production E2E workflow와 완전히 독립되어 있습니다.
- 검색 점수는 텍스트 유사도를 나타내며 accuracy, confidence 또는 고장 확률이 아닙니다.

## 쌍을 이루는 Observation

원본에는 동일한 `SerialNo`를 가진 복수 Observation이 존재합니다. 쌍을 이루는 행의 Feature vector는 서로 다릅니다. Adapter는 모든 원본 행을 개별 Observation으로 보존하고 pair 관련 데이터 품질 metadata를 기록합니다.

행을 병합, 중복 제거, 선별 또는 relabeling하지 않습니다. 공식 자료에는 이러한 Observation이 식별자와 timestamp를 공유하는 이유가 설명되어 있지 않으므로, 이 PoC는 그 생성 원인이나 통계적 독립성을 추론하지 않습니다.

## 데이터 Adapter

`KAMPCNCAdapter`는 Feature 선택이나 상수 열 제거 없이 40개 Process Feature를 모두 매핑합니다. 결정론적인 행 단위 sample ID를 생성하며, 잘못된 label, 누락된 metadata 또는 Feature, 숫자가 아닌 Feature 값, 파싱할 수 없는 timestamp를 허용하지 않고 실패 처리합니다.

Ground Truth는 prediction과 분리하여 표현합니다.

```json
{
  "raw_label": 0,
  "status": "PASS",
  "source_type": "dataset_ground_truth",
  "prediction": false
}
```

## Guidebook 기반 RAG

독립적인 `kamp_cnc_v1` Knowledge Pack은 페이지와 section을 인식하는 Guidebook chunk, 결정론적 signed SHA-256 hashing vector, cosine similarity를 사용합니다. 외부 embedding 또는 LLM API를 호출하지 않으며 Production `bearing_v1`이나 Chroma를 사용하지 않습니다.

Retriever는 다음 상태를 반환합니다.

- Guidebook 근거가 보정된 threshold를 충족하면 `EVIDENCE_FOUND`.
- Guidebook이 요청한 주장을 뒷받침할 수 없으면 `INSUFFICIENT_EVIDENCE`.
- 관련 없는 요청, 자동 제어 요청 또는 유지보수 명령 요청에는 `OUT_OF_SCOPE`.

PASS Observation은 제품 품질이 PASS라는 뜻일 뿐입니다. 이를 “장비 정상” 또는 “고장 없음”으로 확대하지 않습니다. FAIL Observation은 검색 context를 제공하지만 공구 마모나 다른 특정 원인을 입증하지 않습니다.

## KAMP 출처 표기

국문 출처:

> 중소벤처기업부, Korea AI Manufacturing Platform(KAMP), 정밀가공 품질보증 AI 데이터셋, 스마트제조혁신추진단(㈜인터엑스), 2022.12.23.

- KAMP 공식 사이트: https://www.kamp-ai.kr/
- 데이터셋 제공기관: 스마트제조혁신추진단
- 수행기관: ㈜인터엑스
- 등록일: 2022-12-23

Guidebook 이용 안내는 연구 또는 공적 이용 시 KAMP 출처를 표시하고 인용한 내용/문서를 `kamp@kaist.ac.kr`로 보내도록 요청합니다.

## 공개 안전성

재배포 권한을 별도로 확인하지 않았으므로 원본 CSV와 다운로드한 Guidebook PDF는 의도적으로 Git에서 제외했습니다. 다운로드한 PDF에는 문서별 식별자와 다운로드 사용자 정보도 포함되어 있습니다.

Guidebook 원문을 상당량 포함하거나 실제 원본 행 예시를 담은 생성 파일도 제외했습니다.

- `knowledge/kamp_cnc_v1/chunks.json`
- 원문 파생 index로 추가 검토가 필요한 `knowledge/kamp_cnc_v1/index.json`
- `results/adapter_examples.json`
- `results/rag_retrieval_examples.json`

공개 대상에는 구현 코드, contract, 테스트, 재현 가능한 build script, 집계 audit/report, metadata만 포함한 manifest, 이 README가 포함됩니다. 권한이 있는 원본 파일을 사용하여 로컬에서 build를 실행하면 제외된 Knowledge Pack 파일을 재생성할 수 있습니다.

## 로컬 재현

RAG ingestion 단계에는 `pypdf`가 필요합니다. 외부 API credential은 필요하지 않습니다.

```bash
python3 -m unittest discover -s poc/kamp_cnc/tests -v
python3 -m poc.kamp_cnc.scripts.run_adapter_compatibility --output summary
python3 -m poc.kamp_cnc.scripts.build_rag_poc --output ingestion
```

## 검증하지 않은 사항

- CNC ML 성능 또는 일반화
- Paired Observation의 물리적 독립성 또는 생성 원인
- 제품 단위 label 확정
- 외부 기술 Knowledge Source 또는 문서 간 검색
- LLM을 사용한 생성형 답변 합성
- Production 통합
