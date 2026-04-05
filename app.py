import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import json
from datetime import datetime

# ── 페이지 설정 ───────────────────────────────────────
st.set_page_config(
    page_title="JADX 병해충 예보 모형",
    page_icon="🌿",
    layout="wide"
)

# ── 한글 폰트 설정 ─────────────────────────────────────
@st.cache_resource
def setup_font():
    font_dirs = ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts')]
    for d in font_dirs:
        if os.path.exists(d):
            font_files = fm.findSystemFonts(fontpaths=[d])
            for f in font_files:
                if 'Nanum' in f or 'nanum' in f:
                    fm.fontManager.addfont(f)
                    return 'NanumGothic'
    return 'DejaVu Sans'

FONT_NAME = setup_font()
plt.rcParams['font.family'] = FONT_NAME
plt.rcParams['axes.unicode_minus'] = False

# ── 상수 설정 ─────────────────────────────────────────
SPECIES_CONFIG = {
    "네눈쑥가지나방": {
        "name_en": "Ascotis selenaria",
        "t_low": 9.8, "t_opt": 31.0, "t_upp": 37.8,
        "gen1_x": 188.7, "gen2_x": 745.0, "b": 20,
        "risk_1": {"주의": 188.7, "경보": 240.0, "심각": 289.4},
        "risk_2": {"주의": 745.0, "경보": 883.7, "심각": 984.4},
        "ref_julian": (120, 135),
        "track": "A",
        "source": "Choi & Kim 2014 (Crop Protection 66:72-79)"
    },
    "왕담배나방": {
        "name_en": "Helicoverpa armigera",
        "t_low": 10.7, "t_opt": 35.0, "t_upp": 40.0,
        "gen1_x": 300.0, "gen2_x": 900.0, "b": 30,
        "risk_1": {"주의": 300.0, "경보": 400.0, "심각": 500.0},
        "risk_2": {"주의": 900.0, "경보": 1100.0, "심각": 1300.0},
        "ref_julian": (130, 150),
        "track": "A",
        "source": "파라미터 미확정 — 전문가 자문 필요 (임시값)"
    },
    "파밤나방": {
        "name_en": "Spodoptera exigua",
        "t_low": 10.7, "t_opt": 33.0, "t_upp": 38.0,
        "gen1_x": 376.5, "gen2_x": 753.0, "b": 30,
        "risk_1": {"주의": 376.5, "경보": 500.0, "심각": 600.0},
        "risk_2": {"주의": 753.0, "경보": 900.0, "심각": 1050.0},
        "ref_julian": (150, 180),
        "track": "B*",
        "source": "파라미터 미확정 — 전문가 자문 필요 (임시값) / 기산점 설정 방식 자문 필요"
    },
    "조팝나무진딧물": {
        "name_en": "Aphis spiraecola",
        "t_low": 7.2, "t_opt": 25.0, "t_upp": 35.0,
        "gen1_x": 100.0, "gen2_x": 200.0, "b": 15,
        "risk_1": {"주의": 100.0, "경보": 150.0, "심각": 200.0},
        "risk_2": {"주의": 200.0, "경보": 280.0, "심각": 360.0},
        "ref_julian": (100, 130),
        "track": "B",
        "source": "파라미터 미확정 — 모델 구조 자문 필요 (임시값)"
    }
}

STATIONS = {184: "제주", 189: "서귀포", 188: "성산", 185: "고산"}
HISTORY_FILE = "simulation_history.csv"
WEATHER_FILE = "tb_weather_pest.csv"

# ── 핵심 함수 ──────────────────────────────────────────
def sine_dd(tmax, tmin, t_low, t_opt, t_upp):
    sub1 = (tmax - tmin) / 2
    sub2 = (tmax + tmin) / 2
    if abs(sub1) < 1e-9:
        return 0
    q_low  = np.arcsin(np.clip((t_low - sub2) / sub1, -1, 1))
    q_high = np.arcsin(np.clip((t_opt - sub2) / sub1, -1, 1))
    sub3 = sub2 - t_low if tmin > t_low else \
           (1/np.pi)*((sub2-t_low)*(np.pi/2-q_low)+sub1*np.cos(q_low))
    sub4 = (1/np.pi)*((sub2-t_low)*(q_high+np.pi/2)+(t_opt-t_low)*(np.pi/2-q_high)-sub1*np.cos(q_high))
    sub5 = (1/np.pi)*((sub2-t_low)*(q_high-q_low)+sub1*(np.cos(q_high)-np.cos(q_low))+(t_opt-t_low)*(np.pi/2-q_high))
    if tmax > t_upp or tmax < t_low: return 0
    elif tmin > t_opt:               return t_opt - t_low
    elif tmax < t_opt:               return sub3
    else:                            return sub4 if tmin > t_low else sub5

def sigmoid(dd, x_val, b):
    return 1 / (1 + np.exp(-(dd - x_val) / b))

def run_model(weather_df, stn_nm, year, cfg):
    data = weather_df[
        (weather_df['stn_nm'] == stn_nm) &
        (weather_df['crtr_ymd'].astype(str).str[:4] == str(year))
    ].copy().sort_values('crtr_ymd').reset_index(drop=True)

    data['date'] = pd.to_datetime(data['crtr_ymd'], format='%Y%m%d')
    data['jld']  = data['date'].dt.dayofyear

    data['daily_dd'] = data.apply(
        lambda r: sine_dd(r['day_hghst_tp'], r['day_lowst_tp'],
                          cfg['t_low'], cfg['t_opt'], cfg['t_upp']), axis=1
    )
    data['cumdd']     = data['daily_dd'].cumsum()
    data['sig_gen1']  = data['cumdd'].apply(lambda x: sigmoid(x, cfg['gen1_x'], cfg['b']))
    data['sig_gen2']  = data['cumdd'].apply(lambda x: sigmoid(x, cfg['gen2_x'], cfg['b']))
    return data

def get_risk_dates(data, cfg):
    result = {}
    for grade, dd_val in cfg['risk_1'].items():
        hit = data[data['cumdd'] >= dd_val]
        result[f'1화기_{grade}'] = hit.iloc[0]['date'].strftime('%m/%d') + f" (J{int(hit.iloc[0]['jld'])})" if len(hit) > 0 else "미도달"
    for grade, dd_val in cfg['risk_2'].items():
        hit = data[data['cumdd'] >= dd_val]
        result[f'2화기_{grade}'] = hit.iloc[0]['date'].strftime('%m/%d') + f" (J{int(hit.iloc[0]['jld'])})" if len(hit) > 0 else "미도달"
    return result

def save_history(record):
    if os.path.exists(HISTORY_FILE):
        hist = pd.read_csv(HISTORY_FILE)
    else:
        hist = pd.DataFrame()
    hist = pd.concat([hist, pd.DataFrame([record])], ignore_index=True)
    hist.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')

# ── 사이드바 ──────────────────────────────────────────
with st.sidebar:
    st.title("🌿 JADX 병해충 예보")
    st.markdown("---")

    menu = st.radio("메뉴", ["시뮬레이션 실행", "이력 조회", "파라미터 비교"])

# ══ 메뉴 1: 시뮬레이션 실행 ════════════════════════════
if menu == "시뮬레이션 실행":
    st.title("🔬 병해충 예보 모형 시뮬레이션")

    # 데이터 로드
    if not os.path.exists(WEATHER_FILE):
        st.error(f"기상 데이터 파일을 찾을 수 없습니다: {WEATHER_FILE}")
        st.info("Google Drive에서 tb_weather_pest.csv 파일을 앱과 같은 폴더에 복사해주세요.")
        st.stop()

    @st.cache_data
    def load_weather():
        return pd.read_csv(WEATHER_FILE)

    weather_df = load_weather()
    years = sorted(weather_df['crtr_ymd'].astype(str).str[:4].unique().astype(int), reverse=True)

    # ── 입력 패널 ──
    st.subheader("① 기본 설정")
    col1, col2, col3 = st.columns(3)

    with col1:
        species = st.selectbox("해충 종 선택", list(SPECIES_CONFIG.keys()))
    with col2:
        year = st.selectbox("연도", years)
    with col3:
        station = st.selectbox("관측소", list(STATIONS.values()))

    cfg = SPECIES_CONFIG[species].copy()

    # Track 경고
    track_colors = {"A": "success", "B*": "warning", "B": "error"}
    track_msg = {
        "A":  "✅ Track A — 현행 구조 적용 가능",
        "B*": "⚠️ Track B* — 기산점 설정 방식 자문 필요",
        "B":  "❌ Track B — 모델 구조 신규 설계 필요"
    }
    if cfg['track'] == "A":
        st.success(track_msg[cfg['track']])
    elif cfg['track'] == "B*":
        st.warning(track_msg[cfg['track']])
    else:
        st.error(track_msg[cfg['track']])

    st.caption(f"📚 파라미터 출처: {cfg['source']}")

    st.markdown("---")
    st.subheader("② 파라미터 설정 (수정 가능)")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**발육 온도**")
        t_low = st.number_input("T_low (하한온도 ℃)", value=float(cfg['t_low']), step=0.1, format="%.1f")
        t_opt = st.number_input("T_opt (최적온도 ℃)", value=float(cfg['t_opt']), step=0.1, format="%.1f")
        t_upp = st.number_input("T_upp (상한온도 ℃)", value=float(cfg['t_upp']), step=0.1, format="%.1f")

    with col2:
        st.markdown("**세대별 X_Value (DD)**")
        gen1_x = st.number_input("1화기 X_Value", value=float(cfg['gen1_x']), step=1.0, format="%.1f")
        gen2_x = st.number_input("2화기 X_Value", value=float(cfg['gen2_x']), step=1.0, format="%.1f")

    with col3:
        st.markdown("**Sigmoid b값**")
        b_val = st.number_input("b값 (분포 폭)", value=float(cfg['b']), step=1.0, format="%.1f")
        st.caption("⚠ b값은 현재 임의값\n전문가 자문 필요")

    # ── 위험도 임계값 입력 (X_Value와 독립적으로 관리)
    with st.expander("⚙ 위험도 임계값 설정 (기본값: 엑셀 모델 기준)"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("**1화기 임계값 (DD)**")
            r1_jui  = st.number_input("1화기 주의", value=float(cfg['risk_1']['주의']), step=1.0, format="%.1f")
            r1_gyb  = st.number_input("1화기 경보", value=float(cfg['risk_1']['경보']), step=1.0, format="%.1f")
            r1_sim  = st.number_input("1화기 심각", value=float(cfg['risk_1']['심각']), step=1.0, format="%.1f")
        with col_r2:
            st.markdown("**2화기 임계값 (DD)**")
            r2_jui  = st.number_input("2화기 주의", value=float(cfg['risk_2']['주의']), step=1.0, format="%.1f")
            r2_gyb  = st.number_input("2화기 경보", value=float(cfg['risk_2']['경보']), step=1.0, format="%.1f")
            r2_sim  = st.number_input("2화기 심각", value=float(cfg['risk_2']['심각']), step=1.0, format="%.1f")

    memo = st.text_input("메모 (선택)", placeholder="예: 논문 역산값 적용 / 2화기 수정 테스트")

    # ── 실행 버튼 ──
    if st.button("🚀 시뮬레이션 실행", type="primary", use_container_width=True):

        run_cfg = {
            't_low': t_low, 't_opt': t_opt, 't_upp': t_upp,
            'gen1_x': gen1_x, 'gen2_x': gen2_x, 'b': b_val,
            'risk_1': {'주의': r1_jui, '경보': r1_gyb, '심각': r1_sim},
            'risk_2': {'주의': r2_jui, '경보': r2_gyb, '심각': r2_sim},
        }

        with st.spinner("모델 실행 중..."):
            data = run_model(weather_df, station, year, run_cfg)
            risk_dates = get_risk_dates(data, run_cfg)

        # ── 결과 요약 ──
        st.markdown("---")
        st.subheader("③ 위험도 발생일")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1화기**")
            for k, v in {k: v for k, v in risk_dates.items() if '1화기' in k}.items():
                grade = k.split('_')[1]
                color = "🟡" if grade == "주의" else "🟠" if grade == "경보" else "🔴"
                st.metric(f"{color} {k}", v)

        with col2:
            st.markdown("**2화기**")
            for k, v in {k: v for k, v in risk_dates.items() if '2화기' in k}.items():
                grade = k.split('_')[1]
                color = "🟡" if grade == "주의" else "🟠" if grade == "경보" else "🔴"
                st.metric(f"{color} {k}", v)

        # 논문 기준값 비교
        ref_low, ref_high = cfg['ref_julian']
        hit_1 = data[data['cumdd'] >= run_cfg['risk_1']['주의']]
        if len(hit_1) > 0:
            actual_jld = int(hit_1.iloc[0]['jld'])
            if ref_low <= actual_jld <= ref_high:
                st.success(f"✅ 1화기 주의 발령 Julian {actual_jld} — 논문 권장 범위({ref_low}~{ref_high}) 내")
            else:
                diff = actual_jld - ref_low if actual_jld < ref_low else actual_jld - ref_high
                st.warning(f"⚠️ 1화기 주의 발령 Julian {actual_jld} — 논문 권장 범위 대비 {diff:+d}일")

        # ── 그래프 ──
        st.markdown("---")
        st.subheader("④ 그래프")

        tab1, tab2 = st.tabs(["누적 DD + 위험도", "Sigmoid 개체군 곡선"])

        month_ticks = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        month_labels = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']

        with tab1:
            fig, ax = plt.subplots(figsize=(13, 5))
            ax.plot(data['jld'], data['cumdd'], color='#2E75B6', linewidth=2, label='누적 DD')
            colors_risk = [('#FFC000','1화기 주의'), ('#FF8C00','1화기 경보'), ('#FF0000','1화기 심각'),
                           ('#70AD47','2화기 주의'), ('#00B050','2화기 경보')]
            vals = list(run_cfg['risk_1'].values()) + list(run_cfg['risk_2'].values())[:2]
            for (color, label), val in zip(colors_risk, vals):
                ax.axhline(y=val, color=color, linestyle='--', alpha=0.7, linewidth=1.2, label=f'{label} ({val:.1f} DD)')
            ax.axvspan(ref_low, ref_high, alpha=0.08, color='gray', label=f'논문 권장 구간 (J{ref_low}~{ref_high})')
            ax.set_xlabel('월')
            ax.set_ylabel('누적 DD')
            ax.set_title(f'{species} 누적 DD 및 위험도 ({year}년 {station})')
            ax.set_xlim(1, 365)
            ax.set_xticks(month_ticks)
            ax.set_xticklabels(month_labels)
            ax.legend(fontsize=8, loc='upper left')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with tab2:
            fig2, ax2 = plt.subplots(figsize=(13, 5))
            ax2.plot(data['jld'], data['sig_gen1'], color='#2E75B6', linewidth=2, label='1화기 개체군')
            ax2.plot(data['jld'], data['sig_gen2'], color='#70AD47', linewidth=2, label='2화기 개체군')
            for val, label in [(0.1,'주의(10%)'),(0.5,'경보(50%)'),(0.9,'심각(90%)')]:
                ax2.axhline(y=val, color='gray', linestyle=':', alpha=0.5, linewidth=1)
                ax2.text(5, val+0.02, label, fontsize=8, color='gray')
            ax2.axvspan(ref_low, ref_high, alpha=0.08, color='orange', label=f'논문 권장 구간')
            ax2.set_xlabel('월')
            ax2.set_ylabel('개체군 출현 비율 (0~1)')
            ax2.set_title(f'{species} 세대별 개체군 발생 곡선 ({year}년 {station})')
            ax2.set_xlim(1, 365)
            ax2.set_ylim(-0.05, 1.05)
            ax2.set_xticks(month_ticks)
            ax2.set_xticklabels(month_labels)
            ax2.legend(fontsize=9)
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close()

        # ── 이력 저장 ──
        record = {
            "실행일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "종": species, "연도": year, "관측소": station,
            "T_low": t_low, "T_opt": t_opt, "T_upp": t_upp,
            "1화기_X": gen1_x, "2화기_X": gen2_x, "b값": b_val,
            "1화기_주의": risk_dates.get('1화기_주의','미도달'),
            "1화기_경보": risk_dates.get('1화기_경보','미도달'),
            "2화기_주의": risk_dates.get('2화기_주의','미도달'),
            "2화기_경보": risk_dates.get('2화기_경보','미도달'),
            "메모": memo
        }
        save_history(record)
        st.success("✅ 이력 저장 완료")

# ══ 메뉴 2: 이력 조회 ══════════════════════════════════
elif menu == "이력 조회":
    st.title("📋 시뮬레이션 이력")

    if not os.path.exists(HISTORY_FILE):
        st.info("아직 실행 이력이 없습니다.")
    else:
        hist = pd.read_csv(HISTORY_FILE)

        # 필터
        col1, col2 = st.columns(2)
        with col1:
            sel_species = st.multiselect("종 필터", hist['종'].unique().tolist(), default=hist['종'].unique().tolist())
        with col2:
            sel_stn = st.multiselect("관측소 필터", hist['관측소'].unique().tolist(), default=hist['관측소'].unique().tolist())

        filtered = hist[(hist['종'].isin(sel_species)) & (hist['관측소'].isin(sel_stn))]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(filtered)}건")

        # CSV 다운로드
        csv = filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 이력 다운로드 (CSV)", csv, "simulation_history.csv", "text/csv")

# ══ 메뉴 3: 파라미터 비교 ══════════════════════════════
elif menu == "파라미터 비교":
    st.title("📊 파라미터별 결과 비교")

    if not os.path.exists(HISTORY_FILE):
        st.info("실행 이력이 없습니다. 먼저 시뮬레이션을 실행해주세요.")
    else:
        hist = pd.read_csv(HISTORY_FILE)

        sel_species = st.selectbox("종 선택", hist['종'].unique().tolist())
        sel_stn     = st.selectbox("관측소 선택", hist['관측소'].unique().tolist())
        sel_year    = st.selectbox("연도 선택", sorted(hist['연도'].unique().tolist(), reverse=True))

        filtered = hist[
            (hist['종'] == sel_species) &
            (hist['관측소'] == sel_stn) &
            (hist['연도'] == sel_year)
        ].copy()

        if len(filtered) == 0:
            st.info("해당 조건의 이력이 없습니다.")
        else:
            st.subheader(f"{sel_species} / {sel_stn} / {sel_year}년 — {len(filtered)}건")

            # 파라미터별 1화기 주의 발령일 비교
            fig, ax = plt.subplots(figsize=(12, 4))
            labels = [f"b={row['b값']}\nX={row['1화기_X']}\n{row['실행일시'][5:16]}" for _, row in filtered.iterrows()]
            vals_raw = []
            for _, row in filtered.iterrows():
                v = row['1화기_주의']
                if 'J' in str(v):
                    try:
                        jld = int(str(v).split('J')[1].replace(')',''))
                        vals_raw.append(jld)
                    except:
                        vals_raw.append(0)
                else:
                    vals_raw.append(0)

            bars = ax.bar(range(len(vals_raw)), vals_raw, color='#2E75B6', alpha=0.8)
            ref_low, ref_high = SPECIES_CONFIG[sel_species]['ref_julian']
            ax.axhspan(ref_low, ref_high, alpha=0.15, color='orange', label=f'논문 권장 범위 (J{ref_low}~{ref_high})')
            for i, (bar, v) in enumerate(zip(bars, vals_raw)):
                ax.text(bar.get_x() + bar.get_width()/2, v + 1, f'J{v}', ha='center', fontsize=9)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=8)
            ax.set_ylabel('Julian Date (1화기 주의 발령일)')
            ax.set_title(f'파라미터별 1화기 주의 발령일 비교')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            st.dataframe(
                filtered[['실행일시','T_low','T_opt','b값','1화기_X','2화기_X','1화기_주의','1화기_경보','2화기_주의','메모']],
                use_container_width=True, hide_index=True
            )
