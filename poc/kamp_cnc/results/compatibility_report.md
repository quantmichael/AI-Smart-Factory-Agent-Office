# KAMP CNC Adapter 호환성 보고서 — K1-B

## 데이터 계약 및 Adapter

- Contract: `CNCObservation` version `1.0.0`
- Adapter: `KAMPCNCAdapter` version `1.0.0`
- Source: `KAMP`
- Dataset: `정밀가공_품질보증_데이터셋`
- Equipment type: `CNC_PRECISION_MACHINING`
- Stable ID: dataset name, 0부터 시작하는 CSV data-row index, SerialNo, 정규화한 timestamp의 SHA-256

Adapter는 CSV 한 행을 하나의 Observation으로 매핑합니다. Paired row를 병합하거나 Feature를 선택하거나 상수를 제거하거나 label을 변경하지 않으며, paired observation이 존재하는 이유를 추론하지 않습니다.

## Feature 매핑

40개 Process Feature를 모두 유한한 숫자로 보존합니다.

- `spindle_speed`: max, mean, min, std
- `servo_current`: X, Z1, Z2, Z3 × max, mean, min, std
- `servo_load`: X, Z1, Z2, Z3 × max, mean, min, std
- `spindle_load`: max, mean, min, std

K1-A에서 확인한 13개 상수 Feature도 변환된 모든 Observation에 그대로 유지됩니다.

## 정답값(Ground Truth)

- `passorfail=0` → `PASS`
- `passorfail=1` → `FAIL`
- `source_type=dataset_ground_truth`
- `prediction=false`

Ground Truth는 ML prediction이 아닙니다.

## 쌍을 이루는 Observation

Adapter는 99개 paired SerialNo group을 198개의 개별 Observation으로 보존합니다. 각 paired row에는 다음을 기록합니다.

- `paired_serial=true`
- `same_timestamp_pair=true`
- `paired_label_status=PASS_FAIL_PAIR`
- `feature_vector_distinct=true`

제품 단위 label을 선택하거나 추론하지 않습니다.

## 전체 데이터셋 호환성

| 지표 | 결과 |
|---|---:|
| 입력 행 | 1,085 |
| 변환된 Observation | 1,085 |
| PASS | 986 |
| FAIL | 99 |
| Paired Observation 행 | 198 |
| Paired SerialNo group | 99 |
| 검증 실패 | 0 |
| 고유 sample ID | 1,085 |
| 중복 sample ID | 0 |
| Observation당 Feature 값 | 40 |
| 원본 대비 Feature 값 불일치 | 0 |

전체 데이터셋 호환성 판정은 **PASS**입니다.

원본에는 unpaired FAIL row가 없습니다. 따라서 `adapter_examples.json`은 이 제한을 기록하고 일반 FAIL 매핑 예시에 실제 paired FAIL Observation을 사용합니다. Unpaired FAIL code path는 실제 행에서 파생한 유효한 in-memory test fixture로 별도 검증했습니다. 원본 CSV는 수정하지 않았습니다.

## 오류 데이터 즉시 거부(Fail-closed) 검증

Adapter는 다음 경우 `AdapterValidationError`를 발생시킵니다.

- 0 또는 1이 아닌 label
- 필수 metadata 누락
- 필수 Feature column 누락
- 비어 있거나 숫자가 아니거나 NaN 또는 무한대인 Feature 값
- 파싱할 수 없는 timestamp
- 잘못된 row index

잘못된 원본 데이터를 암묵적으로 변환하거나 보정하지 않습니다.

## 테스트

- 실행한 테스트: 15
- 통과: 15
- 실패: 0
- Framework: Python standard-library `unittest`
- Production 테스트 실행: 아니요

테스트 suite는 일반 PASS, 유효한 unpaired FAIL 매핑, paired PASS, paired FAIL, Ground Truth 의미, prediction 분리, 40개 전체 Feature, paired metadata, 결정론적 sample ID, 네 가지 fail-closed case, metadata 누락, 전체 데이터셋 변환을 다룹니다.

## Production 격리

- K1-B에서 변경한 Production code: 없음
- Production DB 기록: 0
- `poc/`에서 Production import: 없음
- 기존 Production 테스트: 변경하거나 실행하지 않음
- 기존 DB, Checkpoint, Memory, Artifact, Chroma, ML model 및 배포 설정: 건드리지 않음

기존 Frontend 파일 2개의 선행 수정과 그 밖의 untracked repository file은 이 PoC 범위 밖에 그대로 남아 있으며 K1-B에서 변경하지 않았습니다.

## 다음 단계 결정

- **K1-B: PASS**
- **K2 CNC RAG PoC: GO** — 검색 과정에서 공식 Guidebook/CSV의 구분을 유지하고 알려진 불일치를 암묵적으로 해소하지 않고 드러내야 합니다.
- **ML Baseline PoC: HOLD** — paired observation의 출처와 통계적 독립성 문제에 대한 공식 처리 방침이 확정될 때까지 보류합니다. Adapter 호환성만으로는 ML 유효성 위험이 해소되지 않습니다.
