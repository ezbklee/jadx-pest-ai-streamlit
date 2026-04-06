SPECIES_CONFIG = {
    "네눈쑥가지나방": {
        "name_en": "Ascotis selenaria",
        "t_low": 9.8, "t_opt": 31.0, "t_upp": 37.8,
        "gen1_x": 188.7, "gen2_x": 745.0, "b": 20,
        "risk_1": {"주의": 188.7, "경계": 240.0, "심각": 289.4},
        "risk_2": {"주의": 745.0, "경계": 883.7, "심각": 984.4},
        "ref_julian": (120, 135),
        "track": "A",
        "source": "Choi & Kim 2014 (Crop Protection 66:72-79)"
    },
    "왕담배나방": {
        "name_en": "Helicoverpa armigera",
        "t_low": 10.7, "t_opt": 35.0, "t_upp": 40.0,
        "gen1_x": 191.0, "gen2_x": 712.0, "b": 30,
        "risk_1": {"주의": 191.0, "경계": 250.0, "심각": 310.0},
        "risk_2": {"주의": 712.0, "경계": 850.0, "심각": 980.0},
        "ref_julian": (130, 150),
        "track": "A",
        "source": "Choi et al. 2023 (JEE 116(5):1689) — T_low=10.7℃, 알43DD+유충287DD+번데기191DD / 제주대 공동연구 ⚠ b값·위험도 임계값은 자문 필요"
    },
    "파밤나방": {
        "name_en": "Spodoptera exigua",
        "t_low": 10.7, "t_opt": 33.0, "t_upp": 38.0,
        "gen1_x": 376.5, "gen2_x": 753.0, "b": 30,
        "risk_1": {"주의": 376.5, "경계": 500.0, "심각": 600.0},
        "risk_2": {"주의": 753.0, "경계": 900.0, "심각": 1050.0},
        "ref_julian": (150, 180),
        "track": "B*",
        "source": "파라미터 미확정 — 전문가 자문 필요 (임시값) / 기산점 설정 방식 자문 필요"
    },
    "조팝나무진딧물": {
        "name_en": "Aphis spiraecola",
        "t_low": 7.2, "t_opt": 25.0, "t_upp": 35.0,
        "gen1_x": 100.0, "gen2_x": 200.0, "b": 15,
        "risk_1": {"주의": 100.0, "경계": 150.0, "심각": 200.0},
        "risk_2": {"주의": 200.0, "경계": 280.0, "심각": 360.0},
        "ref_julian": (100, 130),
        "track": "B",
        "source": "파라미터 미확정 — 모델 구조 자문 필요 (임시값)"
    }
}

STATIONS = {184: "제주", 189: "서귀포", 188: "성산", 185: "고산"}

HISTORY_FILE = "simulation_history.csv"
WEATHER_FILE = "tb_weather_pest.csv"

# 조팝나무진딧물 rm 모델 전용 분기 키
RM_MODEL_SPECIES = "조팝나무진딧물"
