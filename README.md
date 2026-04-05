# JADX 병해충 예보 모형

Streamlit 기반 병해충 발생 예측 시뮬레이션 앱입니다.

## 기능

- **시뮬레이션 실행**: 종·연도·관측소를 선택하고 파라미터를 조정해 발생 예측일 및 위험도를 산출합니다.
- **이력 조회**: 과거 시뮬레이션 결과를 필터링하고 CSV로 내보냅니다.
- **파라미터 비교**: 동일 조건에서 파라미터 변화에 따른 1화기 발령일 차이를 시각화합니다.

## 대상 종

| 종 | 모델 | 상태 |
|---|---|---|
| 네눈쑥가지나방 | Sine DD + Sigmoid | Track A (운영) |
| 왕담배나방 | Sine DD + Sigmoid | Track A (운영) |
| 파밤나방 | Sine DD + Sigmoid | Track B* (자문 필요) |
| 조팝나무진딧물 | rm 기반 모델 | Track B (개발 중) |

## 파일 구조

```
app.py                      # UI (Streamlit)
models/
  __init__.py
  config.py                 # SPECIES_CONFIG, 경로 상수
  sine_model.py             # Sine DD + Sigmoid 모델 (네눈쑥, 왕담배, 파밤)
  rm_model.py               # 조팝나무진딧물 rm 모델 (stub)
tb_weather_pest.csv         # 기상 데이터 (별도 배포)
simulation_history.csv      # 시뮬레이션 이력 (자동 생성)
requirements.txt
```

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

기상 데이터 파일(`tb_weather_pest.csv`)을 앱과 같은 폴더에 위치시킨 후 실행하세요.

## 모델 설명

### Sine DD + Sigmoid (sine_model.py)

- 일별 최고·최저 기온으로 Sine 적산온도(DD)를 계산합니다.
- 누적 DD에 Sigmoid 함수를 적용해 세대별 개체군 출현 비율을 추정합니다.
- 위험도 임계값(주의·경보·심각) 도달일을 Julian Date로 출력합니다.

### rm 모델 (rm_model.py) — 개발 예정

- 조팝나무진딧물의 내적 자연증가율(rm) 기반 개체군 성장 모델입니다.
- 현재 stub 상태이며, 구현 후 `run_rm_model()` 함수 내부를 채워 넣으면 됩니다.
