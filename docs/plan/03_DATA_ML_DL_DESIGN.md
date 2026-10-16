# AI Smart Factory Agent Office

## 03. Data & ML/DL Design

**문서 버전:** v0.1\
**선행 문서:** `01_PROJECT_OVERVIEW.md`, `02_SYSTEM_ARCHITECTURE.md`\
**기준 데이터:** Paderborn University Bearing DataCenter\
**목적:** Reference Dataset의 실제 구조를 기준으로 ML/DL 문제, 전처리,
학습·평가, 추론 출력 및 향후 데이터 교체 인터페이스를 정의한다.

> 주의: 본 문서의 Paderborn 데이터 사양은 공식 Bearing DataCenter 설명을
> 기준으로 작성한다. 실제 다운로드 파일의 내부 변수명과 배열 구조는
> 데이터 확보 후 별도 프로파일링하여 확정한다.

------------------------------------------------------------------------

## 1. 데이터 선정 원칙

본 프로젝트에서 데이터는 ML/DL만 잘 되는 것으로 선정하지 않는다.

최우선 조건은 다음 두 요소가 **같은 설비 진단 도메인에서
결합되는가**이다.

``` text
① Sensor Dataset
        +
② RAG Technical Knowledge
        ↓
AI Diagnosis Workflow
```

현재 Reference 조합:

``` text
Paderborn Bearing Sensor Data
        +
Paderborn Damage Fact Sheets / Measurement Documentation
        +
Bearing / Vibration Diagnosis Technical Documents
        ↓
ML/DL + RAG + LangGraph Agent
```

향후 더 좋은 `Dataset + RAG Corpus` 조합이 발견되면 교체한다.

------------------------------------------------------------------------

## 2. Paderborn Reference Dataset 개요

공식 Bearing DataCenter는 구름베어링 Condition Monitoring을 위한 실험
데이터를 제공한다.

주요 특성:

-   6203 ball bearing 기반 실험
-   6개 healthy bearing state
-   damaged bearing states 포함
-   artificial damage와 accelerated lifetime test에서 발생한 real damage
    포함
-   motor current와 housing vibration을 동기 측정
-   speed, torque, radial load, temperature 보조 측정
-   4개 운전 조건
-   각 setting마다 4초 측정을 20회 수행
-   MATLAB `.mat` 파일 제공
-   bearing damage Fact Sheet 및 measurement log 제공

이 데이터는 ML/DL 학습뿐 아니라 동일 손상에 대한 문서 기반 RAG와 연결할
수 있다는 점이 핵심이다.

------------------------------------------------------------------------

## 3. Test Rig 이해

시험장치의 기본 구성:

``` text
Drive Motor
    ↓
Torque Measurement Shaft
    ↓
Bearing Test Module
    ↓
Flywheel
    ↓
Load Motor
```

주요 측정값:

``` text
Bearing Housing Vibration
Motor Stator Current
Rotational Speed
Torque
Radial Load
Temperature
```

주 진단 대상은 rolling bearing 상태이다.

------------------------------------------------------------------------

## 4. 운전 조건

공식 데이터는 대표적으로 다음 네 운전조건을 사용한다.

  Setting            Speed   Load Torque   Radial Force
  ------------- ---------- ------------- --------------
  N15_M07_F10     1500 rpm        0.7 Nm         1000 N
  N09_M07_F10      900 rpm        0.7 Nm         1000 N
  N15_M01_F10     1500 rpm        0.1 Nm         1000 N
  N15_M07_F04     1500 rpm        0.7 Nm          400 N

실험 중 온도는 대략 45\~50°C 수준으로 유지되었다.

이 운전조건은 모델이 특정 RPM/부하 하나만 외우지 않도록 하는 데
중요하다.

------------------------------------------------------------------------

## 5. 초기 ML/DL 문제 정의

교육성과 프로젝트 완성도를 고려하여 문제를 단계적으로 구성한다.

### Task A --- Healthy vs Damaged

가장 먼저 구현한다.

``` text
Input: vibration signal window
Output:
- healthy
- damaged
```

목적: - 전체 파이프라인 검증 - 전처리 검증 - 모델 학습/추론 API 완성 -
LangGraph의 정상/이상 분기 연결

### Task B --- Fault Category Classification

Task A가 안정화된 후 진행한다.

예:

``` text
healthy
inner-related damage
outer-related damage
other bearing damage
```

실제 클래스는 Paderborn damage metadata를 확인한 후 확정한다.

### Task C --- Anomaly Detection

교육용 확장 실험.

정상 데이터 중심으로 학습하여 평상시와 다른 상태를 탐지한다.

후보: - Isolation Forest - One-Class SVM - Autoencoder

이 Task는 실제 산업현장에서 고장 Label이 부족한 상황을 설명하기에 좋다.

------------------------------------------------------------------------

## 6. 권장 교육 전략

하나의 복잡한 DL 모델만 만드는 것보다 다음 순서가 교육에 적합하다.

``` text
Baseline Feature ML
        ↓
1D Deep Learning
        ↓
Unsupervised Anomaly Detection
        ↓
모델 비교
```

### Baseline ML

후보:

-   Logistic Regression
-   Random Forest
-   XGBoost 또는 Gradient Boosting
-   SVM

입력은 진동 원시 신호가 아니라 추출 Feature를 사용한다.

### DL Baseline

후보:

-   1D CNN

초기 프로젝트에서는 Transformer 계열 모델까지 확장하지 않는다.

이유: - 모델 자체가 프로젝트 중심이 되는 것을 방지 - RAG/LangGraph
학습시간 확보 - 1D CNN만으로도 시계열 DL 학습 경험 확보

### Unsupervised Baseline

후보:

-   Isolation Forest
-   Autoencoder

------------------------------------------------------------------------

## 7. 데이터 처리 Pipeline

``` text
MAT File
   ↓
Dataset Loader
   ↓
Metadata Mapping
   ↓
Signal Channel Selection
   ↓
Signal Validation
   ↓
Windowing
   ↓
Preprocessing
   ↓
Feature Extraction
   ├──────────────→ ML
   │
   └──────────────→ Raw/Normalized Window → DL
```

------------------------------------------------------------------------

## 8. Dataset Profiling 선행 작업

실제 학습 전 반드시 자동 프로파일링 Script를 작성한다.

확인 항목:

-   파일 개수
-   파일명 패턴
-   MAT 내부 Key
-   각 Channel 이름
-   배열 Shape
-   Sampling rate
-   Missing/invalid data
-   Bearing ID
-   Operating condition
-   Damage metadata
-   Healthy/Damaged 분포
-   실제 클래스별 Sample 수

결과는 다음 형태로 저장한다.

``` text
artifacts/data_profile.json
artifacts/data_profile.csv
```

프로파일링 전에는 내부 변수명을 코드에 하드코딩하지 않는다.

------------------------------------------------------------------------

## 9. Windowing

4초 측정 전체를 한 Sample로만 사용하지 않고 일정 길이의 Window로 분할할
수 있다.

예시 설계:

``` text
4 sec measurement
    ↓
fixed-size windows
    ↓
window_001
window_002
window_003
...
```

Window 크기와 overlap은 실제 sampling rate와 실험 결과를 확인하여
결정한다.

후보:

``` text
Window: 0.25 sec / 0.5 sec / 1 sec
Overlap: 0% / 50%
```

### 중요한 Leakage 방지 원칙

같은 원본 측정에서 생성된 Window를 Train과 Test에 동시에 넣지 않는다.

더 나아가 가능하면 **Bearing ID 기준 Group Split**을 적용한다.

``` text
Bearing A windows → Train
Bearing B windows → Validation
Bearing C windows → Test
```

Window를 무작위로 섞어 분할하면 모델 성능이 실제보다 과대평가될 위험이
있다.

------------------------------------------------------------------------

## 10. Signal Preprocessing

초기 후보:

-   NaN / Inf 검사
-   DC offset 제거
-   normalization / standardization
-   필요 시 filtering
-   window segmentation

주파수 기반 분석 실험 시:

-   FFT
-   Power Spectrum
-   Envelope analysis

를 추가할 수 있다.

단, 처음부터 모든 신호처리를 넣지 않는다.

------------------------------------------------------------------------

## 11. Feature Engineering

ML Baseline에서 다음 Feature를 검토한다.

### Time Domain

``` text
mean
standard deviation
RMS
peak
peak-to-peak
crest factor
skewness
kurtosis
```

### Frequency Domain

``` text
dominant frequency
spectral centroid
band energy
frequency-band RMS
spectral peaks
```

### Bearing Diagnostic Feature

향후 베어링 geometry와 shaft speed를 확보하면 characteristic frequency
기반 Feature를 추가할 수 있다.

이 부분은 RAG 기술문서와 연결하기 좋은 포인트다.

------------------------------------------------------------------------

## 12. ML Baseline Pipeline

``` text
Signal Window
     ↓
Feature Extraction
     ↓
Feature Vector
     ↓
Scaler
     ↓
Classifier
     ↓
Probability / Prediction
```

첫 Baseline 권장:

``` text
Random Forest
```

이유: - 교육생이 이해하기 쉬움 - Feature importance 확인 가능 - 빠른
학습 - CPU 환경에서도 충분 - DL 결과와 비교 기준 제공

------------------------------------------------------------------------

## 13. DL Baseline Pipeline

첫 DL 모델:

``` text
1D CNN
```

예시 개념:

``` text
Signal Window
    ↓
Conv1D
    ↓
Activation
    ↓
Pooling
    ↓
Conv1D
    ↓
Pooling
    ↓
Global Pooling
    ↓
Dense
    ↓
Prediction
```

구체적인 layer 수와 kernel size는 데이터 프로파일링 후 결정한다.

------------------------------------------------------------------------

## 14. Unsupervised Anomaly Detection

산업현장 확장성을 설명하기 위한 중요한 실험이다.

``` text
Healthy Data
     ↓
Train Anomaly Model
     ↓
Learn Normal Pattern
     ↓
New Sensor Data
     ↓
Anomaly Score
```

이때 모델은 특정 고장명을 직접 확정하지 않는다.

출력:

``` text
normal
abnormal
anomaly_score
```

그 다음 단계에서 RAG + Agent가 가능한 원인 후보를 탐색한다.

------------------------------------------------------------------------

## 15. Train / Validation / Test

권장 우선순위:

### 1순위

**Bearing ID 기준 Group Split**

### 2순위

Measurement run 기준 Group Split

### 지양

Window 단위 완전 Random Split

운전조건 일반화 실험도 가능하다.

예:

``` text
Train:
N15_M07_F10
N09_M07_F10
N15_M01_F10

Test:
N15_M07_F04
```

이를 통해 새로운 운전조건에 대한 Robustness를 관찰할 수 있다.

------------------------------------------------------------------------

## 16. 평가 Metric

### Binary Classification

-   Accuracy
-   Precision
-   Recall
-   F1-score
-   ROC-AUC
-   Confusion Matrix

특히 이상 상태를 놓치는 문제가 중요하므로 Recall을 함께 본다.

### Multi-class

-   Macro F1
-   Weighted F1
-   Class별 Precision/Recall
-   Confusion Matrix

### Anomaly Detection

-   ROC-AUC
-   PR-AUC
-   Recall
-   False Positive Rate
-   anomaly score distribution

------------------------------------------------------------------------

## 17. 모델 선택 기준

최종 모델은 Accuracy 하나로 선정하지 않는다.

다음 요소를 함께 고려한다.

``` text
성능
+
추론 속도
+
설명 가능성
+
Agent 연결 용이성
+
교육 가치
```

따라서 최고 성능 DL 모델과 별개로 Feature 기반 ML 결과를 UI에서 함께
보여줄 수 있다.

------------------------------------------------------------------------

## 18. Agent 전달용 Standard Analysis Result

ML/DL 계층은 Agent에게 내부 모델 구조를 노출하지 않는다.

표준 Schema 예:

``` json
{
  "analysis_id": "analysis_001",
  "equipment_id": "bearing_test_rig_01",
  "dataset_source": "paderborn",
  "model": {
    "model_id": "rf_v1",
    "model_type": "random_forest",
    "task": "healthy_vs_damaged"
  },
  "operating_condition": {
    "rpm": 1500,
    "load_torque_nm": 0.7,
    "radial_force_n": 1000
  },
  "result": {
    "status": "abnormal",
    "predicted_class": "damaged",
    "confidence": 0.91,
    "anomaly_score": null
  },
  "signal_features": {
    "rms": 0.0,
    "peak": 0.0,
    "kurtosis": 0.0,
    "dominant_frequency": 0.0
  },
  "metadata": {
    "bearing_id": "...",
    "measurement_id": "..."
  }
}
```

------------------------------------------------------------------------

## 19. ML/DL → RAG Query Context

Agent는 분석 결과를 그대로 자연어 Prompt에 던지지 않는다.

구조화된 Context를 만든다.

예:

``` text
Equipment:
6203 rolling bearing test rig

Operating Condition:
1500 rpm / 0.7 Nm / 1000 N radial force

ML Result:
Abnormal bearing condition detected

Confidence:
0.91

Observed Signal Features:
- RMS increased
- Kurtosis elevated
- dominant vibration components: ...

Task:
Retrieve technical evidence relevant to possible bearing damage,
diagnostic checks, and recommended inspection procedures.
```

RAG 검색 결과는 다음 단계 Diagnosis Node에 전달한다.

------------------------------------------------------------------------

## 20. RAG와 ML/DL의 책임 경계

### ML/DL이 하는 일

``` text
패턴 감지
상태 분류
이상 Score
신호 Feature 계산
```

### RAG가 하는 일

``` text
기술적 의미 검색
고장 메커니즘 검색
관련 진단 기준 검색
점검 절차 검색
정비/조치 근거 검색
```

### Agent가 하는 일

``` text
ML 결과 + RAG 근거 결합
가능한 원인 후보 생성
근거 충분성 판단
추가 검색
점검 순서 생성
조치안 생성
```

즉:

``` text
ML/DL = Detect
RAG   = Ground / Explain
Agent = Diagnose / Decide / Coordinate
```

------------------------------------------------------------------------

## 21. 데이터 교체 Interface

새로운 데이터셋은 다음 Interface를 만족하도록 Adapter를 작성한다.

개념 예:

``` python
class SensorDatasetAdapter:
    def list_equipment(self):
        ...

    def list_measurements(self):
        ...

    def load_signal(self, measurement_id):
        ...

    def get_operating_condition(self, measurement_id):
        ...

    def get_label(self, measurement_id):
        ...

    def get_metadata(self, measurement_id):
        ...
```

Paderborn 전용 코드는 `PaderbornAdapter` 안에 격리한다.

------------------------------------------------------------------------

## 22. 모델 교체 Interface

모델도 동일한 방식으로 교체 가능하게 한다.

``` python
class ConditionModel:
    def preprocess(self, signal):
        ...

    def predict(self, signal):
        ...

    def to_analysis_result(self, prediction):
        ...
```

예:

``` text
RandomForestConditionModel
CNNConditionModel
AutoencoderConditionModel
```

모두 `Standard Analysis Result`를 반환한다.

------------------------------------------------------------------------

## 23. 교육생 실습 권장 흐름

``` text
1. 데이터 구조 확인
2. 정상/이상 Signal 시각화
3. RMS 등 기본 Feature 계산
4. FFT 확인
5. Feature Dataset 생성
6. Random Forest 학습
7. 평가 및 Confusion Matrix
8. 1D CNN 학습
9. ML vs DL 비교
10. Autoencoder/Isolation Forest 이상탐지
11. 모델 결과를 API로 제공
12. LangGraph에 연결
13. RAG 근거와 결합
```

이 순서라면 ML/DL 자체가 프로젝트 전체를 잡아먹지 않으면서도 핵심 학습을
경험할 수 있다.

------------------------------------------------------------------------

## 24. 초기 구현 범위 확정

### MVP 필수

-   Paderborn 데이터 프로파일링
-   Vibration Channel 사용
-   Healthy vs Damaged
-   Feature extraction
-   Random Forest Baseline
-   평가
-   Standard Analysis Result
-   추론 함수/API
-   LangGraph 연결

### MVP 이후

-   1D CNN
-   Fault category classification
-   Motor current 활용
-   Vibration + Current Sensor Fusion
-   Autoencoder 또는 Isolation Forest
-   운전조건 일반화 실험
-   Explainability 고도화

------------------------------------------------------------------------

## 25. 데이터 라이선스

Paderborn Bearing DataCenter는 공식 안내상 **CC BY-NC 4.0** 조건으로
제공된다.

비상업적 학술 사용은 출처 표시를 전제로 허용되며, 상업적 사용은 별도
문의가 필요하다.

따라서:

``` text
교육 프로젝트 / 연구 Prototype
→ 출처 및 라이선스 명시

향후 상업 서비스
→ Paderborn 데이터 자체를 서비스 데이터로 사용하는 문제는 별도 검토
```

플랫폼 구조는 데이터 교체가 가능하도록 유지한다.

------------------------------------------------------------------------

## 26. 완료 기준

`03_DATA_ML_DL_DESIGN` 단계의 실제 개발 완료 기준:

-   [ ] Dataset 다운로드 및 구조 확인
-   [ ] 자동 프로파일링 결과 생성
-   [ ] Label mapping 확정
-   [ ] Train/Validation/Test split 확정
-   [ ] 정상/이상 Signal 시각화
-   [ ] Feature extraction 구현
-   [ ] Random Forest Baseline 학습
-   [ ] 평가 결과 저장
-   [ ] Standard Analysis Result 구현
-   [ ] 단일 Sample inference 성공
-   [ ] Backend 또는 LangGraph에서 inference 호출 성공

------------------------------------------------------------------------

## 27. 다음 문서

다음 산출물:

**`04_RAG_DESIGN.md`**

여기서는 본 프로젝트에서 가장 중요한 두 축 중 두 번째인 RAG를 상세
설계한다.

구체적으로:

-   어떤 기술문서를 확보할지
-   Paderborn Fact Sheet와 외부 기술문서를 어떻게 연결할지
-   문서 출처 등급
-   PDF/HTML Parsing
-   Chunking 전략
-   Metadata Schema
-   Embedding
-   Vector DB
-   Hybrid Retrieval 여부
-   Reranking
-   ML/DL 결과 기반 Query 생성
-   Citation
-   RAG 품질 평가
-   Hallucination 방지
-   데이터셋 교체 시 Knowledge Pack 교체 구조

를 정의한다.
