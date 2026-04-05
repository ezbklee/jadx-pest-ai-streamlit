"""
조팝나무진딧물 전용 rm(내적 자연증가율) 기반 모델
현재 상태: stub — 구현 예정
"""

import streamlit as st


def run_rm_model(weather_df, stn_nm, year, cfg):
    """
    rm 기반 개체군 성장 모델 (조팝나무진딧물 전용).

    Parameters
    ----------
    weather_df : pd.DataFrame
        기상 데이터 (app.py에서 로드한 전체 데이터프레임)
    stn_nm : str
        관측소 이름
    year : int
        시뮬레이션 연도
    cfg : dict
        SPECIES_CONFIG에서 가져온 파라미터 딕셔너리

    Returns
    -------
    None
        현재는 stub이므로 None을 반환합니다.
    """
    # TODO: rm 모델 구현
    #   1. 일별 기온 데이터로 내적 자연증가율(rm) 계산
    #   2. 개체군 밀도 N(t) = N0 * exp(rm * t) 또는 로지스틱 모델 적용
    #   3. 발생 예측일 및 위험도 산출
    #   4. run_model()과 동일한 형태의 DataFrame 반환

    st.warning("조팝나무진딧물 rm 모델은 개발 중입니다.")
    return None
