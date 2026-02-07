import streamlit as st
import pandas as pd
import numpy as np
import requests as req
import folium
import streamlit_folium as sf
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import matplotlib.pyplot as plt
from folium.plugins import MiniMap, Fullscreen, HeatMap
import json
import requests
from folium.features import DivIcon
from matplotlib import rc
import plotly.express as px
import seaborn as sns
import statsmodels.api as sm


rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(
    layout='wide',
    page_title='Smoke',
    page_icon='🚭'
)

# ====[사이드바] 부분====
with st.sidebar:

    col1, col2 = st.columns([1,5])

    # 로고 부분(좌측)
    with col1 :
        st.image('https://cdn-icons-png.flaticon.com/512/2103/2103633.png', width=50)
    # 텍스트 부분(우측)
    with col2 :
        st.markdown('서울시 흡연율')

    # 사이드바에 option_menu UI 배치
    option_menu_side =  option_menu(
        menu_title='메뉴 선택',
        menu_icon='cast',
        options=['개요', '데이터 분석', '결과'],
        icons=['speedometer2', 'bar-chart-line', 'gear'],
        default_index=0,
        styles={
            # container : 메뉴 탭들을 감싸는 전체 공간
             # padding : 요소 내부의 여백(현재는 0으로 여백이 없으며 !important는 해당 스타일을 우선 적용)
             # background-color : 배경색(컬러 GEX코드 값으로 설정 가능)
            'container': {'padding': '10!important', 'background-color' : '#fafafa'},
            'icon' : {'color': 'red', 'font-size' : '18px'},
            # nav-link : 메뉴 탭 내부 관련 설정
             # text-align : 텍스트 정렬
             # --hover-color : 메뉴에 마우스 오버시 변경되는 색상(#eee는 옅은 회색)
            'nav-link': {'font-size':'16px', 'text-align': 'left', 
                         'margin':'0px','--hover-color':'#eee'},
            # nav-link-selected : 메뉴 탭이 선택되었을 때의 설정(#02ab21는 진한 녹색) 
            'nav-link-selected': {'background-color': 'black'}
        }

    )

@st.cache_data
def load_lottie_json(url):
    res = req.get(url)
    # status_code : <Response [200]> 에서 []안의 수치값 확인

    if res.status_code != 200:
        return st.error('통신 에러 발생')
    return res.json()



# ================ 메인화면 ==================
# 1) 대시보드 선택 시
if option_menu_side == '개요':

    st.title('개요')


    col1, col2 = st.columns([1,1])
    # --------------------------------------------------------------------------------
    # 1. 데이터 준비 (작성자님의 데이터프레임이 있다고 가정)
    # --------------------------------------------------------------------------------

    # 2. 서울시 지도 데이터(GeoJSON) 불러오기 (GitHub에서 실시간 로딩)
    # --------------------------------------------------------------------------------
    # 서울시 자치구 경계 좌표가 들어있는 파일 주소입니다. (가장 많이 쓰는 소스)
    with col1:

        geo_url = 'https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json'
        response = requests.get(geo_url)
        seoul_geo = response.json()
        final_df = pd.read_csv('module/data/final_df.csv', encoding='utf-8')

        # 1. 지도에 라벨(구이름) 달기위한 함수
        def make_text(text, color='white', size=11):  # 기본값을 white, 11로 변경
            return DivIcon(
                icon_size=(100, 20),
                icon_anchor=(50, 10),
                html=f'''
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
                '''
            )
        # --------------------------------------------------------------------------------
        # 3. Folium 지도 그리기 (Choropleth)
        # --------------------------------------------------------------------------------
        # (1) 기본 지도 생성 (서울 시청 중심 좌표)
        m = folium.Map(
            location=[37.5665, 126.9780], 
            zoom_start=11, 
            tiles='cartodbpositron' # 깔끔한 배경 스타일 (OpenStreetMap보다 분석용으로 좋음)
        )

        # (2) 단계구분도(색칠) 레이어 추가
        folium.Choropleth(
            geo_data=seoul_geo,             # 지도 경계 데이터
            data=final_df,                        # 분석할 데이터프레임
            columns=['명칭', '흡연'], # [지역명 컬럼, 수치 컬럼]
            key_on='feature.properties.name', # GeoJSON 파일 안에 있는 지역명 키 값 (이거 건드리면 안됨!)
            fill_color='YlOrRd',            # 색상 (Yellow-Orange-Red: 빨갈수록 높음)
            fill_opacity=0.7,               # 투명도
            line_opacity=0.2,               # 경계선 투명도
            legend_name='현재 흡연율 (%)'     # 범례 이름
        ).add_to(m)


        # 2. 반복문으로 25개 구 한 번에 추가하기
        # seoul_geo['features'] 자체가 일종의 리스트입니다.
        for feature in seoul_geo['features']:
            # 이름 꺼내기
            name = feature['properties']['name']

            # 좌표 계산 (seoul_geo데이터에 있는 구별 위도와 경도 평균값)
            coords = np.array(feature['geometry']['coordinates'][0])
            center_lat = coords[:, 1].mean()
            center_lon = coords[:, 0].mean()

            # 지도에 추가 (여기서 함수 사용!)
            folium.Marker(
                location=[center_lat, center_lon],
                icon=make_text(name) # <-- "이름(name)으로 라벨 만들어줘"
            ).add_to(m)


        # --------------------------------------------------------------------------------
        # 4. Streamlit 화면에 띄우기
        # --------------------------------------------------------------------------------
        st.header("🗺️ 서울시 자치구별 흡연율 지도")

        sf.st_folium(m, use_container_width=True)


    # 전체 데이터프레임
    with col2:
        st.header("서울시 자치구별 데이터")
        final_df.index += 1 
        st.dataframe(final_df, column_config={'흡연':'흡연율(%)', '녹지' : '1인당 녹지면적(m^2)', '도보생활권공원' : '1인당 공원면적(m^2)',
                                              '스트레스' : '스트레스(%)', '우울감' : '우울감(%)', '금연치료센터' : '10만명당 금연치료센터(개)', '주거면적' : '1인당 주거면적(m^2)',
                                              '1인가구' : '1인가구(%)', '음주' : '음주(%)', '고위험음주' : '고위험음주(%)', '소득' : '평균연봉(단위:백만원)',
                                              '금연시도율' : '금연시도율(%)', '걷기운동' : '걷기운동(%)', '중고강도운동' : '중고강도운동(%)', '비만' : '비만율(%)'},
                     use_container_width=True, height=800,width = 1300 )




elif option_menu_side == '데이터 분석':
    st.title("데이터 분석")

    final_df = pd.read_csv("module/data/final_df.csv")

    df = pd.DataFrame(final_df)

    # 지역구(명칭), 흡연(흡연율) 컬럼 제외한 selectbox
    df_data = df.drop(columns=["명칭", "흡연"])

    # selectbox
    select = st.selectbox(label="변수 선택", options=df_data.columns)

    # 산점도 차트 : plotly scatter 사용
    fig = px.scatter(
        df,
        x=select, # x축 : 선택한 변수
        y="흡연", # y축 : 흡연율
        hover_name="명칭",
        hover_data=["흡연", select], # 마우스 오버 시 지역구와 선택한 변수
        trendline="ols",
        color=select, # 선택한 변수 값으로 색상 달라짐
        color_continuous_scale="Viridis",
        title=f"흡연율과 {select}의 상관관계",
        labels={"흡연": "흡연율(%)", select: select},
    )

    fig.update_yaxes(title_text="흡\n연\n율\n(%)")
    fig.update_layout(height=550, margin=dict(l=40, r=40, t=60, b=40)) # 차트 크기
    st.plotly_chart(fig, use_container_width=True)

    # 상관계수
    corr_method = "pearson" # 상관계수 계산 이론
    r = df[["흡연", select]].corr(method=corr_method).iloc[0, 1]
    direction = "비례" if r > 0 else "반비례" # 상관계수 +면 비례, -면 반비례
    # strength = "약함" if abs(r) < 0.3 else ("중간" if abs(r) < 0.6 else "강함")
    st.info(f"선택 변수 **{select}**는 흡연율과 **{direction}**, 상관계수 **{r:.2f}**")




elif option_menu_side == '결과':
    final_df = pd.read_csv('module/data/final_df.csv')
    final_df.columns = final_df.columns.str.strip()

    numeric_df = final_df.select_dtypes(include='number')
    corr = numeric_df.corr()

    target = "흡연"
    smoking_corr = corr[[target]].drop(index=target)

    rank_table = smoking_corr.reset_index()
    rank_table.columns = ['변수', '상관계수']
    rank_table['절댓값'] = rank_table['상관계수'].abs()
    rank_table = rank_table.sort_values(by='상관계수', key=abs, ascending=False)
    rank_table['순위'] = range(1, len(rank_table)+1)
    rank_table = rank_table[['순위', '변수', '상관계수']]

    st.title("결과")

    '---'


    col1, col2 =st.columns([1,1])

    with col1 :

    # ================= 히트맵 =================
        fig1, ax1 = plt.subplots(figsize=(6,8))

        sns.heatmap(
            smoking_corr,
            annot=True,
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            fmt=".2f",
            linewidths=2,
            ax=ax1,

        )

        st.markdown(
            "<p style='font-size:20px; text-align:center;'>흡연율과 요소별 히트맵</p>",
            unsafe_allow_html=True
        )



        st.pyplot(fig1)

    with col2 :

    # ================= 표 =================


        st.markdown(
            "<p style='font-size:20px; text-align:center;'>상관계수 순위</p>",
            unsafe_allow_html=True
        )

        st.dataframe(rank_table.reset_index(drop=True),
            use_container_width=True,
            hide_index=True, height=525)



    # ================= 바 차트 =================
    fig2, ax2 = plt.subplots(figsize=(10,6))

    ax2.barh(
        rank_table['변수'],
        rank_table['상관계수']
    )

    ax2.axvline(0, color='red')
    ax2.invert_yaxis()

    ''

    st.pyplot(fig2)
