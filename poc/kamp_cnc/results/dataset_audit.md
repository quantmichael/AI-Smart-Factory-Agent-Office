# KAMP CNC 데이터셋 감사 — K1-A

## 범위 및 근거 원칙

- 값과 구조: CSV를 Source of Truth로 사용합니다.
- 의미, label 정의, 명시된 수집/가공 방식: 공식 Guidebook을 Reference로 사용합니다.
- 이 감사는 read-only로 수행했습니다. Adapter, ML 학습, RAG, Production test 또는 DB write를 수행하지 않았습니다.

## 1. 데이터셋 무결성

- Shape: **1,085행 × 43열**.
- Dtype: `SerialNo`와 `ReceivedDateTime`은 `object`로 로드되며, 40개 process feature는 모두 `float64`, `passorfail`은 `int64`입니다. 모든 `ReceivedDateTime` 값은 datetime으로 정상 파싱됩니다.
- Missing value: **0**.
- 전체 행 중복: **0**.
- 관측 기간: **2022-08-23 03:14:36.906 — 2022-08-25 10:14:44.102**.
- 관측일별 행 수: 2022-08-23 = 337, 2022-08-24 = 338, 2022-08-25 = 410.
- Label: `0`과 `1`만 존재합니다.
- 매핑: `0 = PASS / 양품`, `1 = FAIL / 불량`이며 Guidebook과 일치합니다.
- PASS: **986 (90.8756%)**.
- FAIL: **99 (9.1244%)**.
- Class ratio: **986:99 = 9.9596:1**.

## 2. SerialNo 및 정답값(Ground Truth)

- 고유 `SerialNo`: **986**.
- `SerialNo` 기준 첫 행을 제외한 중복 행: **99**.
- 1회 등장 제품: **887**; 2회 등장 제품: **99**; 2회를 초과해 등장하는 제품은 없습니다.
- 반복되는 99개 `SerialNo` group은 모두 group 내 `ReceivedDateTime`이 정확히 같습니다.
- 반복되는 99개 group은 모두 process-feature vector가 다르므로 전체 행 중복이 아닙니다.
- 반복되는 99개 group은 모두 `passorfail=0`과 `passorfail=1`을 함께 포함합니다: **충돌 식별자 99개 / 영향받는 행 198개**.
- 대표 사례: `20220823-0000210`, `20220823-0000219`, `20220823-0000231`. 각각 두 행의 timestamp가 같고 label은 `[0, 1]`입니다.
- CSV와 Guidebook은 이러한 pair가 존재하는 이유를 설명하지 않습니다. 원인, 중복 제거 규칙 또는 대체 label을 추론하지 않았습니다.

Guidebook은 `SerialNo`를 제품 번호로 정의하고 한 행이 한 제품을 나타낸다고 설명합니다. 따라서 같은 시간에 반복되고 label이 충돌하는 구조에서는 제한 없는 제품 단위 Ground Truth contract를 확정할 수 없습니다. `SerialNo`는 제품 번호가 fold를 넘나들지 않도록 하는 필수 ML grouping key로 사용할 수 있지만, grouping만으로 모순된 label이 해결되지는 않습니다.

## 3. Feature 계약

### 메타데이터

- `SerialNo`
- `ReceivedDateTime`

### SpindleSpeed

- `SpindleSpeed_max`, `SpindleSpeed_mean`, `SpindleSpeed_min`, `SpindleSpeed_std`

### ServoCurrent

- X: `ServoCurrent_X_max`, `ServoCurrent_X_mean`, `ServoCurrent_X_min`, `ServoCurrent_X_std`
- Z1: `ServoCurrent_Z1_max`, `ServoCurrent_Z1_mean`, `ServoCurrent_Z1_min`, `ServoCurrent_Z1_std`
- Z2: `ServoCurrent_Z2_max`, `ServoCurrent_Z2_mean`, `ServoCurrent_Z2_min`, `ServoCurrent_Z2_std`
- Z3: `ServoCurrent_Z3_max`, `ServoCurrent_Z3_mean`, `ServoCurrent_Z3_min`, `ServoCurrent_Z3_std`

### ServoLoad

- X: `ServoLoad_X_max`, `ServoLoad_X_mean`, `ServoLoad_X_min`, `ServoLoad_X_std`
- Z1: `ServoLoad_Z1_max`, `ServoLoad_Z1_mean`, `ServoLoad_Z1_min`, `ServoLoad_Z1_std`
- Z2: `ServoLoad_Z2_max`, `ServoLoad_Z2_mean`, `ServoLoad_Z2_min`, `ServoLoad_Z2_std`
- Z3: `ServoLoad_Z3_max`, `ServoLoad_Z3_mean`, `ServoLoad_Z3_min`, `ServoLoad_Z3_std`

### SpindleLoad

- `SpindleLoad_max`, `SpindleLoad_mean`, `SpindleLoad_min`, `SpindleLoad_std`

### 정답값(Ground Truth)

- `passorfail`

### 분산 및 동일 Feature 확인 결과

상수 column은 **13개**입니다.

- 상수 30.3: `ServoCurrent_Z2_max`, `ServoLoad_Z2_max`, `ServoCurrent_Z2_mean`, `ServoLoad_Z2_mean`, `ServoCurrent_Z2_min`, `ServoLoad_Z2_min`.
- 상수 0.0: `SpindleSpeed_min`, `ServoLoad_X_min`, `ServoCurrent_Z2_std`, `ServoLoad_Z2_std`, `SpindleLoad_min`.
- 상수 40.4: `ServoCurrent_Z3_min`, `ServoLoad_Z3_min`.

명시적 규칙인 고유 값 비율 ≤10% 및 최빈값/차빈값 빈도비 >19를 적용했을 때, 상수가 아닌 추가 near-zero-variance feature는 발견되지 않았습니다. 상수가 아닌 Feature pair 중 정확히 동일한 것도 없습니다. 동일한 column pair는 모두 위 상숫값 group으로 설명됩니다.

## 4. Guidebook 교차 검증

### 일치 항목

- 1,085행 및 43열.
- PASS 986 및 FAIL 99.
- `passorfail`: 0 = 양품, 1 = 불량.
- `SerialNo`: object 및 제품 번호.
- max / mean / min / std 기반 Feature family.
- 숫자형 상수 13개. 이들과 object column 2개를 제거하면 Guidebook workflow와 같이 28개 column이 남습니다.
- 모든 CSV timestamp는 Guidebook 유효 기간인 2022-08-23부터 2022-08-27 사이에 있습니다.
- PLC/sensor 수집, 10–100 ms 간격 raw sampling, 제품 단위 feature engineering은 공식 Guidebook의 설명이며 최종 집계 CSV만으로 독립적으로 입증할 수는 없습니다.

### Guidebook 최종 9개 변수

1. `SpindleSpeed_max`
2. `ServoLoad_Z1_max`
3. `ServoCurrent_X_mean`
4. `ServoCurrent_X_std`
5. `ServoLoad_X_std`
6. `SpindleLoad_max`
7. `upper_mold_temp1`
8. `SpindleLoad_mean`
9. `SpindleLoad_std`

### 불일치 항목

1. `upper_mold_temp1`은 실제 43-column CSV에 **존재하지 않습니다**. 다른 변수로 대체하지 않았습니다.
2. 명시된 수집 기간은 2022-08-27에 끝나지만 실제 존재하는 마지막 timestamp는 2022-08-25 10:14:44.102입니다. 행은 명시된 기간 안에 있지만 마지막 이틀의 날짜는 포함하지 않습니다.
3. Guidebook은 한 행이 한 제품을 나타내며 `SerialNo`가 제품 번호라고 설명합니다. CSV에는 같은 시간의 행 두 개와 충돌 label을 가진 제품 번호가 99개 있습니다.
4. Guidebook의 SerialNo 고유성 90.9%는 `986 / 1,085`와 일치하지만, 충돌하는 99개 group의 생성 이유와 Ground Truth 처리 방식은 문서화되어 있지 않습니다.

## 5. 데이터 누출 위험 및 안전한 평가 설계

1. **Random row split — 높음:** 같은 `SerialNo`와 timestamp가 train과 test 양쪽에 들어갈 수 있습니다.
2. **Ground Truth 충돌 — 치명적:** 반복되는 모든 `SerialNo`에 두 label이 모두 존재하므로 암묵적으로 중복 제거하거나 relabeling해서는 안 됩니다.
3. **시간적 의존성 — 높음:** 관측일이 3일뿐이어서 무작위 혼합이 날짜 또는 batch drift를 감출 수 있습니다.
4. **Feature selection leakage — 높음:** Guidebook의 T-test selection은 train/test split 전에 수행됩니다. 이 순서를 재사용하면 평가 label이 selection에 노출됩니다.
5. **SMOTE leakage — split 전에 수행하면 치명적:** SMOTE는 training partition에만 적용해야 합니다. Guidebook은 row split 후 적용하지만 해당 row split은 group-safe하지 않습니다.
6. **Preprocessing leakage — 높음:** imputation, outlier threshold, constant filtering, scaling/normalization, feature selection은 각 training partition에서만 fit해야 합니다.

안전한 설계: 먼저 충돌하는 99개 label에 대한 공식 처리 규칙을 확보합니다. 동일한 `SerialNo`의 모든 행은 하나의 group으로 유지하고, sample size가 허용하면 forward temporal holdout을 사용합니다. 모든 preprocessing 및 selection 단계는 training fold 안에서 수행하고, SMOTE는 split 이후 training data에만 적용합니다. Class-aware metric과 불확실성을 함께 보고합니다.

## 6. PoC 적합성

| 목적 | 평가 | 이유 |
|---|---|---|
| CNC Adapter PoC | **GOOD** | Adapter가 모든 행을 보존하고 label을 결정하지 않은 채 충돌을 노출한다면 raw schema와 행 단위 값을 사용할 수 있습니다. |
| Ground Truth Context PoC | **LIMITED** | 0/1의 의미는 공식적이지만 제품 식별자 99개에 모순된 Ground Truth가 있습니다. |
| CNC RAG PoC | **LIMITED** | Guidebook은 유용하지만 답변에서 `upper_mold_temp1` 및 label 불일치를 밝혀야 합니다. |
| 단순 ML Baseline PoC | **LIMITED** | 공식 label 처리와 group/temporal leakage 통제를 마련한 뒤에만 가능합니다. |
| DNN 성능 평가 | **NOT RECOMMENDED** | 데이터가 작고 불균형하며 관측일이 3일뿐이고 해결되지 않은 제품 단위 label 충돌이 있습니다. |
| Production/일반화 주장 | **NOT RECOMMENDED** | 독립적인 site/machine/time holdout이 없고 Ground Truth가 해결되지 않았습니다. |

## 7. 판정

- **K1-A: PASS** — 읽기 전용 감사가 완료되었으며 확인된 모든 불일치를 기록했습니다. 이는 데이터셋이 Production 준비를 마쳤다는 의미가 아닙니다.
- **K1-B Adapter Implementation: GO** — 모든 행을 보존하고, `SerialNo`를 합치거나 label을 추론하지 않으며, contract에 충돌 상태를 드러내야 합니다. Ground Truth 충돌에 대한 공식 해결 전에는 ML 성능 평가를 시작하지 않습니다.
