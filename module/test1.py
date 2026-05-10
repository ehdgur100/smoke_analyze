import streamlit as st
import pandas as pd
import numpy as np
import folium
import streamlit_folium as sf
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
from folium.plugins import MiniMap, Fullscreen, HeatMap
import json
import requests
from folium.features import DivIcon
from matplotlib import rc
import plotly.express as px
import seaborn as sns
import statsmodels.api as sm
import koreanize_matplotlib  # ✨ 이 줄을 새로 추가!

# ========================== 기본 설정 =============================

# 페이지 기본 설정
st.set_page_config(layout="wide", page_title="Smoke", page_icon="🚭")

# 한글 깨짐 방지
# rc("font", family="Malgun Gothic")
# plt.rcParams["axes.unicode_minus"] = False


# 세션 초기화
if "saved_var" not in st.session_state:
    st.session_state["saved_var"] = "녹지"


# ========================================= 함수 ==============================================
# 데이터 불러오기(캐시)
@st.cache_data
def read_file():
    return pd.read_csv("module/data/final_df.csv")


# 서울 자치구별 위도경도값 데이터 가져오는 함수(캐시)
@st.cache_data
def seoul_json(
    geo_url="https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json",
):
    response = requests.get(geo_url)
    seoul_geo = response.json()
    return seoul_geo


# 개요 흡연율 지도 함수
def smoke_map(seoul_geo):
    #  데이터 준비(함수 호출)
    final_df = read_file()

    #  지도에 라벨(구이름) 달기위한 함수
    def make_text(text, color="white", size=11):  # 기본값을 white, 11로 변경
        return DivIcon(
            icon_size=(100, 20),
            icon_anchor=(50, 10),
            html=f"""
                <div style="
                    font-size: {size}pt;
                    font-weight: 900;
                    color: {color};

                    /* 핵심: 그림자 대신 4방향 테두리를 줘서 글자를 선명하게 만듦 */
                    text-shadow: -1px -1px 0 #000, 
                                  1px -1px 0 #000, 
                                 -1px  1px 0 #000, 
                                  1px  1px 0 #000;

                    text-align: center;
                    white-space: nowrap; /* 글자 줄바꿈 금지 (한 줄로 나오게) */
                ">
                    {text}
                </div>
            """,
        )

    # ===================== Folium 지도 그리기 =======================
    # 지도 생성 (서울 시청 중심 좌표)
    m = folium.Map(
        location=[37.5665, 126.9780],
        zoom_start=11,
        tiles="cartodbpositron",  # 깔끔한 배경 스타일 (OpenStreetMap보다 분석용으로 좋음)
    )

    # 단계구분도(색칠) 레이어 추가
    folium.Choropleth(
        geo_data=seoul_geo,  # 지도 경계 데이터
        data=final_df,  # 분석할 데이터프레임
        columns=["명칭", "흡연"],  # [지역명 컬럼, 수치 컬럼]
        key_on="feature.properties.name",  # GeoJSON 파일 안에 있는 지역명 키 값
        fill_color="YlOrRd",  # 색상 (Yellow-Orange-Red: 빨갈수록 높음)
        fill_opacity=0.7,  # 투명도
        line_opacity=0.2,  # 경계선 투명도
        legend_name="현재 흡연율 (%)",  # 범례 이름
    ).add_to(m)

    # === 반복문으로 지도에 구이름 찍어주기 ===
    # seoul_geo['features'] 자체가 일종의 리스트
    for feature in seoul_geo["features"]:
        # 이름 꺼내기
        name = feature["properties"]["name"]

        # 좌표 계산 (seoul_geo데이터에 있는 구별 위도와 경도 평균값)
        coords = np.array(feature["geometry"]["coordinates"][0])
        center_lat = coords[:, 1].mean()
        center_lon = coords[:, 0].mean()

        # 지도에 추가 (여기서 함수 사용!)
        folium.Marker(
            location=[center_lat, center_lon],
            icon=make_text(name),  # <-- "이름(name)으로 라벨 만들어줘"
        ).add_to(m)
    return m


# 사용자 선택값을 세션값으로 바꾸는 함수
def update_sel():
    st.session_state["saved_var"] = st.session_state["select"]


# =========================================================== 전체 화면 구성 =========================================================================

# ================================= [왼쪽 사이드바] 부분 =======================================
with st.sidebar:
    # 좌우 구역 나누기
    col1, col2 = st.columns([1, 5])

    # 로고 부분(좌측)
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=50)
    # 텍스트 부분(우측)
    with col2:
        st.markdown("서울시 흡연율")

    # ================== 사이드바에 option_menu UI 배치 ======================
    option_menu_side = option_menu(
        menu_title="메뉴 선택",
        menu_icon="cast",
        options=["개요", "데이터 분석", "결과"],
        icons=["speedometer2", "bar-chart-line", "gear"],
        default_index=0,
        styles={
            # container : 메뉴 탭들을 감싸는 전체 공간
            # padding : 요소 내부의 여백(현재는 0으로 여백이 없으며 !important는 해당 스타일을 우선 적용)
            # background-color : 배경색(컬러 GEX코드 값으로 설정 가능)
            "container": {"padding": "10!important", "background-color": "#fafafa"},
            "icon": {"color": "red", "font-size": "18px"},
            # nav-link : 메뉴 탭 내부 관련 설정
            # text-align : 텍스트 정렬
            # --hover-color : 메뉴에 마우스 오버시 변경되는 색상(#eee는 옅은 회색)
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            # nav-link-selected : 메뉴 탭이 선택되었을 때의 설정(#02ab21는 진한 녹색)
            "nav-link-selected": {"background-color": "black"},
        },
    )


# =================================================== 메인화면 ============================================================

# ============================ 옵션 메뉴 : 개요 ===================================
if option_menu_side == "개요":

    st.title("개요")

    # 탭버튼 추가
    tab1, tab2 = st.tabs(["지도", "데이터"])

    #  데이터 준비(함수 호출)
    final_df = read_file()
    # ====================== 탭1 '지도' 선택 ============================
    with tab1:
        st.header("🗺️ 서울시 자치구별 흡연율 지도")

        # ==========지도 함수 호출==================
        m = smoke_map(seoul_json())

        # Streamlit 화면에 지도 띄우기
        sf.st_folium(m, use_container_width=True, key="smoke")

    # ====================== 탭2 '히트맵과 표' 선택 ============================
    with tab2:
        st.header("서울시 자치구별 데이터")
        final_df.index += 1  # 인덱스 1부터 보여주기
        # 전체 데이터프레임 컬럼명 변경
        st.dataframe(
            final_df,
            column_config={
                "흡연": "흡연율(%)",
                "녹지": "1인당 녹지면적(m²)",
                "도보생활권공원": "1인당 공원면적(m²)",
                "스트레스": "스트레스(%)",
                "우울감": "우울감(%)",
                "금연치료센터": "10만명당 금연치료센터(개)",
                "주거면적": "1인당 주거면적(m²)",
                "1인가구": "1인가구(%)",
                "음주": "음주(%)",
                "고위험음주": "고위험음주(%)",
                "소득": "평균연봉(단위:백만원)",
                "금연시도율": "금연시도율(%)",
                "걷기운동": "걷기운동(%)",
                "중고강도운동": "중고강도운동(%)",
                "비만": "비만율(%)",
            },
            use_container_width=True,
            height=800,
            width=1300,
        )


# ============================ 옵션 메뉴 : 데이터 분석 ===================================
elif option_menu_side == "데이터 분석":
    st.title("데이터 분석")

    #  데이터 준비(함수 호출)
    final_df = read_file()

    df = pd.DataFrame(final_df)

    # 지역구(명칭), 흡연(흡연율) 컬럼 제외한 selectbox
    df_data = df.drop(columns=["명칭", "흡연"])
    saved = st.session_state.get("saved_var")

    if saved in df_data.columns:
        # 있으면 그 위치(index)를 user_index로
        user_index = list(df_data.columns).index(saved)
    else:
        # 없으면(데이터가 바뀌었거나 오타면) 0으로
        user_index = 0

    # selectbox
    # 키를 넣으면 세션에 자동으로 값 저장
    select = st.selectbox(
        label="변수 선택",
        options=df_data.columns,
        index=user_index,
        key="select",
        on_change=update_sel,
    )  # onchange : 값이 바뀌면 실행

    # 산점도 차트 : plotly scatter 사용
    fig = px.scatter(
        df,
        x=select,  # x축 : 선택한 변수
        y="흡연",  # y축 : 흡연율
        hover_name="명칭",
        hover_data=["흡연", select],  # 마우스 오버 시 지역구와 선택한 변수
        trendline="ols",  # (선형 회귀) 추세선 추가
        color=select,  # 선택한 변수 값으로 색상 달라짐
        color_continuous_scale="Viridis",
        title=f"흡연율과 {select}의 상관관계",
        labels={"흡연": "흡연율(%)", select: select},
    )

    fig.update_yaxes(title_text="흡\n연\n율\n(%)")  # \n 줄바꿈
    fig.update_layout(height=550, margin=dict(l=40, r=40, t=60, b=40))  # 차트 크기
    st.plotly_chart(fig, use_container_width=True)

    # 상관계수
    corr_method = "pearson"  # 상관계수 계산 이론
    r = df[["흡연", select]].corr(method=corr_method).iloc[0, 1]
    direction = "양(+)의 상관관계" if r > 0 else "음(-)의 상관관계"
    st.info(
        f"선택 변수 **{select}**은(는) 흡연율과 **{direction}**, 상관계수 **{r:.2f}**"
    )


# ============================ 옵션 메뉴 : 결과 ===================================
elif option_menu_side == "결과":

    # 1) 데이터 불러오기 + 전처리
    final_df = read_file()
    final_df.columns = final_df.columns.str.strip()

    # 숫자 컬럼만 추출
    numeric_df = final_df.select_dtypes(include="number")

    # 상관관계 계산
    corr = numeric_df.corr()

    # 흡연 기준 상관계수만 추출
    target = "흡연"
    smoking_corr = corr[[target]].drop(index=target)

    # 2 ) 상관계수 순위표 만들기
    rank_table = smoking_corr.reset_index()
    rank_table.columns = ["변수", "상관계수"]
    rank_table["절댓값"] = rank_table["상관계수"].abs()

    # 절대값 기준 정렬( 영향력 큰 순 )
    rank_table = rank_table.sort_values(by="상관계수", key=abs, ascending=False)

    # 순위 추가
    rank_table["순위"] = range(1, len(rank_table) + 1)
    rank_table = rank_table[["순위", "변수", "상관계수"]]

    # 화면 제목
    st.title("결과")
    tab1, tab2 = st.tabs(["히트맵과 표", "바"])

    # ====================== 탭1 '히트맵과 표' 선택 ============================
    with tab1:

        # 히트맵, 표, 바 차트
        col1, col2 = st.columns([1, 1])

        # ======= 히트맵 ========
        with col1:

            _, center, _ = st.columns([1, 3, 1])

            with center:
                st.subheader("흡연율과 요소별 히트맵")

            fig1, ax1 = plt.subplots(figsize=(6, 8))

            sorted_heatmap = smoking_corr.loc[rank_table["변수"]]

            # sns = seaborn(시각화 라이브러리)
            sns.heatmap(
                sorted_heatmap,
                annot=True,
                cmap="coolwarm",
                vmin=-1,
                vmax=1,
                fmt=".2f",
                linewidths=2,
                ax=ax1,
            )

            st.pyplot(fig1)

        # ======== 표 =========

        with col2:

            _, center, _ = st.columns([1, 2, 1])

            with center:
                st.subheader("상관계수 순위표")

            st.dataframe(
                rank_table.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                height=525,
            )

    # ====================== 탭2 '바' 선택 ============================
    with tab2:
        # ============= 바 차트 =============
        fig2, ax2 = plt.subplots(figsize=(8, 4))

        ax2.barh(rank_table["변수"], rank_table["상관계수"])

        ax2.axvline(0, color="red")
        ax2.invert_yaxis()
        ""
        st.pyplot(fig2)
