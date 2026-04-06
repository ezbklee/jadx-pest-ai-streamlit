"""
Sine DD + Sigmoid 모델
대상 종: 네눈쑥가지나방, 왕담배나방, 파밤나방
"""

import numpy as np
import pandas as pd
import os
from .config import HISTORY_FILE


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

    # 귤굴나방 특이 처리: 5일 이동평균 ≥ bug_active 온도 이전은 DD=0
    if cfg.get('bug_active') is not None:
        avg_tp = (data['day_hghst_tp'] + data['day_lowst_tp']) / 2
        ma5 = avg_tp.rolling(5, min_periods=1).mean()
        first_active = ma5[ma5 >= cfg['bug_active']].index.min()
        if pd.notna(first_active):
            data.loc[data.index < first_active, 'daily_dd'] = 0.0
            data.loc[first_active, 'daily_dd'] = 0.0   # reset 지점 포함

    data['cumdd']    = data['daily_dd'].cumsum()
    data['sig_gen1'] = data['cumdd'].apply(lambda x: sigmoid(x, cfg['gen1_x'], cfg['b']))
    data['sig_gen2'] = data['cumdd'].apply(lambda x: sigmoid(x, cfg['gen2_x'], cfg['b']))
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
