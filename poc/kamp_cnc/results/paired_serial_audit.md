# KAMP CNC 중복 Serial 감사 — K1-A.1

## 범위

- 입력: `poc/kamp_cnc/data/raw/정밀가공_품질보증_데이터셋.csv`
- Pair: 동일한 `SerialNo`가 정확히 두 번 등장하는 경우.
- 차이의 부호: `FAIL - PASS`.
- 식별자 및 label column은 Feature 비교에서 제외합니다.
- 원본 행을 수정하거나 제거하지 않았습니다. ML 학습, Adapter 구현, RAG 작업, Production test 또는 DB write를 수행하지 않았습니다.

## 1. 쌍 표본

- 두 행으로 구성된 `SerialNo` group: **99**.
- 동일한 `SerialNo`: **99/99**.
- Pair 내 동일한 `ReceivedDateTime`: **99/99**.
- PASS 1개와 FAIL 1개로 정확히 구성: **99/99**.
- 40개 Feature 값이 모두 같고 label만 다른 pair: **0**.
- 하나 이상의 Feature가 다른 pair: **99**.

99개 pair는 모두 서로 다른 Feature vector입니다. 이는 값 수준의 차이만 입증합니다. CSV만으로는 두 행이 독립적인 물리적 측정인지 확인할 수 없으며 식별자와 timestamp가 같은 이유도 설명할 수 없습니다.

## 2. 차이 계산 방법

- 평균 차이와 중앙값 차이는 `FAIL - PASS`를 사용합니다.
- 절대 차이는 99개 pair의 `abs(FAIL - PASS)` 평균 및 중앙값으로 요약합니다.
- 대칭 상대 차이는 `(FAIL-PASS) / ((abs(FAIL)+abs(PASS))/2)`입니다. 양쪽이 모두 0이라 분모가 0인 경우는 0으로 기록합니다.
- Feature 간 표준화 차이는 pair의 절대 차이를 198개 paired row에서 계산한 해당 Feature의 모집단 표준편차로 나눕니다.
- 전체 pair magnitude는 상수가 아닌 27개 Feature의 표준화 차이에 대한 RMS입니다.
- 상수는 표준화 해석에서 제외합니다.
- “거의 동일” 또는 “명확히 다름”을 나누는 임의의 이진 threshold를 사용하지 않습니다. 대신 정확한 일치 여부, 관측 순위 및 분포 quantile을 보고합니다.

## 3. Feature 차이

### Pair 내에서 값이 다른 Feature

| Feature | PASS 평균 | FAIL 평균 | 평균 차이 | 중앙값 차이 | 평균 절대 차이 | 평균 절대 상대 차이 | FAIL > PASS | FAIL < PASS | 동일 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SpindleSpeed_max | 2226.326 | 2220.815 | -5.510 | 0.000 | 5.510 | 0.2481% | 0 | 49 | 50 |
| ServoCurrent_X_max | 1131.547 | 1148.527 | 16.980 | -13.150 | 39.607 | 3.4347% | 49 | 50 | 0 |
| SpindleSpeed_mean | 1188.958 | 1206.075 | 17.117 | -14.015 | 41.306 | 3.4347% | 49 | 50 | 0 |
| ServoCurrent_X_mean | 150.142 | 140.463 | -9.680 | -5.025 | 9.680 | 6.7482% | 0 | 99 | 0 |
| SpindleSpeed_std | 868.046 | 868.108 | 0.062 | 7.730 | 8.680 | 1.0000% | 50 | 49 | 0 |
| ServoCurrent_X_std | 149.755 | 140.173 | -9.582 | -6.393 | 9.582 | 6.7482% | 0 | 99 | 0 |
| ServoLoad_X_std | 18.276 | 19.653 | 1.377 | 1.227 | 1.377 | 7.1775% | 99 | 0 | 0 |
| ServoLoad_Z3_std | 195.614 | 210.509 | 14.895 | 6.428 | 14.895 | 7.1775% | 99 | 0 | 0 |
| SpindleLoad_max | 31692.244 | 32649.202 | 956.957 | 1495.535 | 956.957 | 2.9561% | 99 | 0 | 0 |
| SpindleLoad_mean | 3323.665 | 3110.528 | -213.136 | -110.330 | 213.136 | 6.7482% | 0 | 99 | 0 |
| SpindleLoad_std | 4880.808 | 5245.014 | 364.206 | 257.349 | 364.206 | 7.1775% | 99 | 0 | 0 |

### 모든 pair에서 동일하게 유지되는 비상수 Feature

다음 16개 Feature는 데이터셋 전체에서는 값이 변하지만 99개 모든 pair의 PASS와 FAIL 사이에서는 정확히 같습니다.

- `ServoCurrent_Z1_max`, `ServoCurrent_Z3_max`
- `ServoLoad_X_max`, `ServoLoad_Z1_max`, `ServoLoad_Z3_max`
- `ServoCurrent_Z1_mean`, `ServoCurrent_Z3_mean`
- `ServoLoad_X_mean`, `ServoLoad_Z1_mean`, `ServoLoad_Z3_mean`
- `ServoCurrent_X_min`, `ServoCurrent_Z1_min`, `ServoLoad_Z1_min`
- `ServoCurrent_Z1_std`, `ServoCurrent_Z3_std`, `ServoLoad_Z1_std`

### 해석에서 제외한 상수 Feature

- `ServoCurrent_Z2_max`, `ServoLoad_Z2_max`
- `ServoCurrent_Z2_mean`, `ServoLoad_Z2_mean`
- `SpindleSpeed_min`, `ServoCurrent_Z2_min`, `ServoCurrent_Z3_min`
- `ServoLoad_X_min`, `ServoLoad_Z2_min`, `ServoLoad_Z3_min`
- `ServoCurrent_Z2_std`, `ServoLoad_Z2_std`, `SpindleLoad_min`

### 척도 보정 후 차이가 가장 큰 Feature

평균 paired absolute difference를 paired row 전체에서 계산한 Feature 표준편차로 나눈 값의 순위입니다.

1. `SpindleLoad_max`: 1.2966
2. `SpindleSpeed_max`: 1.0416
3. `ServoCurrent_X_mean`: 1.0052
4. `SpindleLoad_std`: 0.7079
5. `SpindleLoad_mean`: 0.3982

## 4. Pair 단위 차이

- 서로 다른 Feature 수: 최소 10, 중앙값 10, 최대 11.
- 정확히 10개 Feature가 다른 경우: **50 pairs**.
- 정확히 11개 Feature가 다른 경우: **49 pairs**.
- 동일한 Feature 수: 50개 pair는 30개, 49개 pair는 29개.
- 추가되는 11번째 차이는 `SpindleSpeed_max`이며 50개 pair에서는 같고 49개 pair에서는 FAIL이 더 낮습니다.

전체 표준화 RMS magnitude 분포:

| Quantile | Magnitude |
|---:|---:|
| 최솟값 | 0.4211 |
| 10% | 0.4402 |
| 25% | 0.4462 |
| 중앙값 | 0.4512 |
| 75% | 0.5890 |
| 90% | 0.5949 |
| 최댓값 | 0.6154 |

관측된 pair 중 가장 가까운 것은 0.4211의 `20220824-0000062`이고 가장 다른 것은 0.6154의 `20220823-0000210`입니다. 이는 관측 순위이며 threshold 기반의 “같음/다름” 범주가 아닙니다. 가장 가까운 pair도 10개 Feature가 다릅니다.

### 정확한 paired pattern

차이는 두 가지 정확한 비율 pattern으로 나타납니다.

- **50 pairs:** FAIL/PASS ratio는 `ServoCurrent_X_mean`, `ServoCurrent_X_std`, `SpindleLoad_mean`에서 0.97, `ServoLoad_X_std`, `ServoLoad_Z3_std`, `SpindleLoad_std`, `SpindleLoad_max`에서 1.05, `SpindleSpeed_max`에서 1.00, `ServoCurrent_X_max`, `SpindleSpeed_mean`에서 0.98, `SpindleSpeed_std`에서 1.01입니다.
- **49 pairs:** ratio는 `ServoCurrent_X_mean`, `ServoCurrent_X_std`, `SpindleLoad_mean`에서 0.90, `ServoLoad_X_std`, `ServoLoad_Z3_std`, `SpindleLoad_std`에서 1.10, `SpindleLoad_max`에서 1.01, `SpindleSpeed_max`에서 0.995, `ServoCurrent_X_max`, `SpindleSpeed_mean`에서 1.05, `SpindleSpeed_std`에서 0.99입니다.

이는 PASS와 FAIL 행이 체계적으로 다른 Feature vector라는 강한 근거입니다. 동시에 이들의 생성 또는 수집 출처가 확인되기 전에는 통계적으로 독립이라고 가정해서는 안 된다는 뜻이기도 합니다. 이러한 정확한 pattern의 생성 원인은 추론하지 않았습니다.

## 5. Guidebook 방향성 교차 검증

Guidebook은 `SpindleLoad_max`, `SpindleLoad_std`와 양의 관계, `SpindleSpeed_max`, `ServoCurrent_X_mean`과 음의 관계를 설명합니다.

| Feature | 기대 방향 | 일치 | 불일치 | 동일 | Paired 평균 차이 | Paired 중앙값 차이 |
|---|---|---:|---:|---:|---:|---:|
| SpindleLoad_max | FAIL > PASS | 99/99 | 0 | 0 | 956.957 | 1495.535 |
| SpindleLoad_std | FAIL > PASS | 99/99 | 0 | 0 | 364.206 | 257.349 |
| SpindleSpeed_max | FAIL < PASS | 49/99 | 0 | 50 | -5.510 | 0.000 |
| ServoCurrent_X_mean | FAIL < PASS | 99/99 | 0 | 0 | -9.680 | -5.025 |

동일하지 않은 paired change는 모두 Guidebook 방향과 일치합니다. 세 변수는 모든 pair에서 일치하고 `SpindleSpeed_max`는 49개 pair에서 일치하며 50개에서는 변하지 않습니다. 이는 방향성 일치일 뿐 causality 또는 물리적 독립성을 입증하지 않습니다.

## 6. 해석

**판정: DISTINCT_OBSERVATIONS**

모든 pair의 Feature vector가 다르고 변경된 Feature가 10개 또는 11개이며 label만 다른 pair는 없습니다. 차이는 체계적이고 Guidebook의 네 가지 방향성과 일치합니다. 따라서 label만 변경된 중복 행이 아니라 별도의 행 단위 Observation으로 취급할 근거가 있습니다.

이 판정은 저장된 Feature 값에만 한정됩니다. 동일한 식별자, 동일한 timestamp, 정확한 두 가지 비율 pattern은 출처 및 데이터 품질 측면에서 여전히 해결되지 않은 문제입니다. 현재 파일만으로 두 행이 별도의 물리적 생산 측정이라는 점을 입증할 수 없습니다.

## 7. ML 영향

- **독립적인 row 사용: 출처 확인 전 HOLD.** Row는 서로 다른 vector지만 통계적 또는 물리적 독립성은 확립되지 않았습니다.
- **SerialNo Group Split: 필수.** Pair의 두 행은 같은 fold에 있어야 합니다.
- **Random row split: 허용하지 않음.** Paired record가 train과 evaluation set 양쪽에 들어가 성능을 부풀릴 수 있습니다.
- **Data-quality flag: 필수.** 원본 label을 변경하지 않고 `paired_serial=true`, `same_timestamp=true`, `conflicting_labels=true`를 기록합니다.
- Paired-row 생성/수집 규칙이 확인되거나 실험 범위를 Production 일반화 평가가 아닌 dataset-behavior PoC로 명시한 뒤에만 baseline을 시작해야 합니다.

## 8. 다음 단계 결정

- **CNC Adapter PoC: GO.** 각 원본 행을 보존하고 pair/conflict metadata를 노출합니다. 행을 병합하거나 제품 단위 label을 추론하지 않습니다.
- **ML Baseline PoC: HOLD.** 출처 확인과 paired 구조에 대한 문서화된 처리 방침을 기다립니다.
