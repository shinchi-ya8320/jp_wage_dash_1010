import plotly.express as px
import streamlit as st
import pandas as pd
import pydeck as pdk
from streamlit.caching import ThreadLocalCacheInfo
from streamlit.config import get_option

#タイトルの設定
st.title('日本賃金データダッシュボード')

#データフレームのインポート
#日本語のcsvファイルは読み込みにエラーが発生する
#列名が日本語ならエンコーディングでshift_jisを指定してあげる
df_jp_ind = pd.read_csv('雇用_医療福祉_一人当たり賃金_全国_全産業.csv', encoding='shift_jis')
df_jp_category = pd.read_csv('雇用_医療福祉_一人当たり賃金_全国_大分類.csv', encoding='shift_jis')
df_pref_ind = pd.read_csv('雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv', encoding='shift_jis')


#日本の地図にヒートマップ
#上に全国賃金を表示したい
#ヒートマップのヘッダー
st.header('2019年:1人当たり平均賃金のヒートマップ')

#県庁所在地をその地域の代表とする
df_lat_lon = pd.read_csv('pref_lat_lon.csv')

#賃金データと県庁所在地のデータを結合する
#列名を変更する
df_lat_lon = df_lat_lon.rename(columns={'pref_name': '都道府県名'})

#df_pref_indの年齢が年齢計となってて、集計年が2019となっているものを抜き出す
df_pref_map = df_pref_ind[(df_pref_ind['年齢'] == '年齢計') & (df_pref_ind['集計年'] == 2019)]

#マージめそっとを使ってデータの結合を行う
df_pref_map = pd.merge(df_pref_map, df_lat_lon, on='都道府県名')

#1人当たり賃金を正規化する
#正規化とは最小値を0、最大値を1になるように変換する
df_pref_map['一人当たり賃金（相対値）'] = ((df_pref_map['一人当たり賃金（万円）'] - df_pref_map['一人当たり賃金（万円）'].min()) / (df_pref_map['一人当たり賃金（万円）'].max() - df_pref_map['一人当たり賃金（万円）'].min()))
#df_pref_map

#ビューの設定
#東京の県庁所在地をビューとする

view = pdk.ViewState(
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,
    pitch=40.5
)


#レイヤーの設定
layer = pdk.Layer(
    "HeatmapLayer",
    data=df_pref_map,
    opacity=0.4,
    get_position=['lon','lat'],
    threshold=0.3,
    get_weight = '一人当たり賃金（相対値）'
)

#レンダリング
layer_map = pdk.Deck(
    layers=layer,
    initial_view_state=view
)

st.pydeck_chart(layer_map)

show_df = st.checkbox('Show DataFrame')

if show_df == True:
    st.write(df_pref_map)


st.header('集計年別の一人当たり賃金（万円）の推移')

#全国の平均賃金の推移
df_ts_mean = df_jp_ind[df_jp_ind['年齢'] == '年齢計']

#df_ts_mean内のカラム名のリネーム
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）': '全国_一人当たり賃金（万円）'})

#都道府県ごとの平均賃金の推移
df_pref_mean = df_pref_ind[df_pref_ind['年齢'] == '年齢計']

#都道府県別にチェックボックスを作成したいため
#都道府県のユニークな値を抽出する
pref_list = df_pref_mean['都道府県名'].unique()

#都道府県のセレクトボックスの作成
option_pref = st.selectbox(
    '都道府県',
    (pref_list)
)

#都道府県べつで出したい。都道府県名がセレクトボックスで選択されたものと一緒の物を
#df_pref_meanのなかから取り出す
df_pref_mean = df_pref_mean[df_pref_mean['都道府県名'] == option_pref]

#グラフの作成

#データの結合
#都道府県別の賃金データフレームと全国賃金のデータフレームを結合
df_mean_line = pd.merge(df_ts_mean, df_pref_mean, on='集計年')
df_mean_line = df_mean_line[['集計年', '全国_一人当たり賃金（万円）', '一人当たり賃金（万円）']]

#インデックスを作成する
df_mean_line = df_mean_line.set_index('集計年')

#折れ線グラフを作成する
st.line_chart(df_mean_line)

#バブルチャートの作成

st.header('年齢階級別の全国一人当たり平均賃金（万円）')

df_mean_bubble = df_jp_ind[df_jp_ind['年齢'] != '年齢計']

#ぷろっとりーえくすぷれす
#散布図やバブルチャートはscatter関数を使う
fig1 = px.scatter(df_mean_bubble,
    x='一人当たり賃金（万円）',
    y='年間賞与その他特別給与額（万円）',
    range_x=[150,700],
    range_y=[0,150],
    #バブルサイズ
    size='所定内給与額（万円）',
    #バブルサイズのマックス
    size_max=38,
    color='年齢',
    animation_frame='集計年',
    animation_group='年齢'
    
)

st.plotly_chart(fig1)


st.header('産業別賃金推移')

#集計年をユニークな値として持たせておく
year_list = df_jp_category['集計年'].unique()

option_year = st.selectbox(
    '集計年',
    (year_list)
    )

#賃金の種類をユニークに持たせておく
wage_list = ['一人当たり賃金（万円）', '所定内給与額（万円）', '年間賞与その他特別給与額（万円）']

option_wage = st.selectbox(
    '賃金の種類',
    (wage_list)
)

#上の二つのセレクトボックスで選択した物を表示するための処理
df_mean_categ = df_jp_category[(df_jp_category['集計年'] == option_year )]

#賃金リストごとの最大値を取得する処理
max_x = df_mean_categ[option_wage].max() + 50

#棒グラフの作成
fig2 = px.bar(
    df_mean_categ,
    x=option_wage,
    y='産業大分類名',
    color='産業大分類名',
    animation_frame='年齢',
    range_x=[0,max_x],
    orientation='h',
    width=800,
    height=500,
)

st.plotly_chart(fig2)


#だっしゅぼーどをデプロイするときの
#データの出店元を記載する
st.text('出典：RESAS（地域経済分析システム）')
st.text('本結果はRESAS（地域経済分析システム）を加工して作成')


#gitはバージョン管理システムのこと
#githubはwebサービス
#
