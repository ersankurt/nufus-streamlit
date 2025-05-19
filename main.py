import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests
import pydeck as pdk


st.set_page_config(page_title="Türkiye Nüfus Haritası", layout="wide")


# yıllara göre nüfus
df_nufus = pd.read_excel("dataset/yıllara göre il nufus .xlsx", engine="openpyxl", header=2)
df_nufus = df_nufus[~df_nufus["İl\nProvinces"].isna()]
df_nufus = df_nufus[df_nufus["İl\nProvinces"] != "Toplam-Total"]
df_nufus = df_nufus.loc[:, ["İl\nProvinces", "Unnamed: 21", "Unnamed: 22", "Unnamed: 23", "Unnamed: 24", "Unnamed: 25"]]
df_nufus.columns = ["İl", "2019", "2020", "2021", "2022", "2023"]

df_nufus.head(8)
df_nufus.tail(11)
df_nufus = df_nufus.reset_index(drop=True)
df_nufus = df_nufus.drop(index=range(81, 89))  # [81-88] rows drop
df_nufus.index = range(1, len(df_nufus) + 1)   # il plaka denliği için df düzenlemesi


years = ["2019", "2020", "2021", "2022", "2023"]
for i in range(len(years)):
    for j in range(i + 1, len(years)):
        y1 = years[i]
        y2 = years[j]
        df_nufus[f"Değişim_{y1}_{y2}"] = df_nufus[y2].astype(float) - df_nufus[y1].astype(float)
df_nufus.index = range(1, len(df_nufus) + 1)   # il plaka denliği için df düzenlemesi



#yıllara göre yoğunluk
# (Nüfus Yoğunluğu = Toplam Nüfus / Yüzölçümü (km²))
df_yogunluk = pd.read_excel("dataset/yillara gore illerin yillik nufus artis hizi ve nufus yogunlugu.xlsx", header=2)
df_yogunluk = df_yogunluk[["İl-Provinces", "Unnamed: 30","Unnamed: 31", "Unnamed: 32", "Unnamed: 33", "Unnamed: 34"]]
df_yogunluk.columns = ["İl", "Yoğunluk_2019", "Yoğunluk_2020", "Yoğunluk_2021", "Yoğunluk_2022", "Yoğunluk_2023"]

df_yogunluk = df_yogunluk.iloc[2:83]  # 2 dahil, 83 hariç üst sınır
df_yogunluk = df_yogunluk.reset_index(drop=True)
df_yogunluk.index = range(1, len(df_yogunluk) + 1)


yoğunluk_yillar = ["Yoğunluk_2019", "Yoğunluk_2020", "Yoğunluk_2021", "Yoğunluk_2022", "Yoğunluk_2023"]
for i in range(len(yoğunluk_yillar)):
    for j in range(i + 1, len(yoğunluk_yillar)):
        y1 = yoğunluk_yillar[i]
        y2 = yoğunluk_yillar[j]
        df_yogunluk[f"Yoğunluk_Değişim_{y1[-4:]}_{y2[-4:]}"] = df_yogunluk[y2].astype(float) - df_yogunluk[y1].astype(float)



# df and df_yoğunluk marge
df = df_nufus.merge(df_yogunluk, on="İl", how="left")
df.index = range(1, len(df_yogunluk) + 1)



# 1. Plaka eşleme sözlüğü
il_plaka_map = {
    'Adana': 1, 'Adıyaman': 2, 'Afyonkarahisar': 3, 'Ağrı': 4, 'Amasya': 5, 'Ankara': 6,
    'Antalya': 7, 'Artvin': 8, 'Aydın': 9, 'Balıkesir': 10, 'Bilecik': 11, 'Bingöl': 12,
    'Bitlis': 13, 'Bolu': 14, 'Burdur': 15, 'Bursa': 16, 'Çanakkale': 17, 'Çankırı': 18,
    'Çorum': 19, 'Denizli': 20, 'Diyarbakır': 21, 'Edirne': 22, 'Elazığ': 23, 'Erzincan': 24,
    'Erzurum': 25, 'Eskişehir': 26, 'Gaziantep': 27, 'Giresun': 28, 'Gümüşhane': 29,
    'Hakkari': 30, 'Hatay': 31, 'Isparta': 32, 'Mersin': 33, 'İstanbul': 34, 'İzmir': 35,
    'Kars': 36, 'Kastamonu': 37, 'Kayseri': 38, 'Kırklareli': 39, 'Kırşehir': 40, 'Kocaeli': 41,
    'Konya': 42, 'Kütahya': 43, 'Malatya': 44, 'Manisa': 45, 'Kahramanmaraş': 46, 'Mardin': 47,
    'Muğla': 48, 'Muş': 49, 'Nevşehir': 50, 'Niğde': 51, 'Ordu': 52, 'Rize': 53, 'Sakarya': 54,
    'Samsun': 55, 'Siirt': 56, 'Sinop': 57, 'Sivas': 58, 'Tekirdağ': 59, 'Tokat': 60,
    'Trabzon': 61, 'Tunceli': 62, 'Şanlıurfa': 63, 'Uşak': 64, 'Van': 65, 'Yozgat': 66,
    'Zonguldak': 67, 'Aksaray': 68, 'Bayburt': 69, 'Karaman': 70, 'Kırıkkale': 71,
    'Batman': 72, 'Şırnak': 73, 'Bartın': 74, 'Ardahan': 75, 'Iğdır': 76, 'Yalova': 77,
    'Karabük': 78, 'Kilis': 79, 'Osmaniye': 80, 'Düzce': 81
}

# 2. Eşleme ile yeni sütun oluştur
df["plaka"] = df["İl"].map(il_plaka_map)
df.head()
print(df[df["plaka"].isna()][["İl"]])

#Geojson (Türkiye map)
with open("dataset/tr-cities.json", encoding="utf-8") as f:
    turkey_geo = json.load(f)
print(turkey_geo["features"][0]["properties"])


#Türkiye sehir merkez koordinatları.
with open("dataset/cities_of_turkey.json", encoding="utf-8") as f:
    cities_data = json.load(f)

# Dict'e çevir: { "Adana": [lat, lon], ... }
city_coords = {
    city["name"]: [float(city["latitude"]), float(city["longitude"])]
    for city in cities_data
}

# DF'e ekle
df["lat"] = df["İl"].map(lambda x: city_coords.get(x, [None, None])[0])
df["lon"] = df["İl"].map(lambda x: city_coords.get(x, [None, None])[1])




#STREAMLİT
st.title("Türkiye Nüfus ve Yoğunluk Değişimi Haritası")


st.markdown(
    """
    <style>
    .main {
        background-color: #000000;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#  Yeni  yapı
veri_turu = st.sidebar.radio("Göstermek istediğiniz veri türü:", ["Nüfus Değişimi", "Yoğunluk Değişimi"])

if veri_turu == "Nüfus Değişimi":
    fark_sutunlari = [col for col in df.columns if col.startswith("Değişim_") and not col.startswith("Yoğunluk")]
else:
    fark_sutunlari = [col for col in df.columns if col.startswith("Yoğunluk_Değişim_")]
secilen_fark = st.sidebar.selectbox("2D harita için Yıl Aralığı Seçin:", fark_sutunlari)

import io

# Seçilen veri türüne göre sütunları filtrele
indirilecek_df = df[["İl", secilen_fark]]

# Excel dosyasını bellekte oluştur
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    indirilecek_df.to_excel(writer, index=False, sheet_name="Veri")

excel_data = excel_buffer.getvalue()

with st.sidebar.expander("📊 Seçilen Verinin Özeti"):
    st.write("Ortalama:", int(df[secilen_fark].mean()))
    st.write("Toplam:", int(df[secilen_fark].sum()))
    st.write("Min:", int(df[secilen_fark].min()))
    st.write("Max:", int(df[secilen_fark].max()))


# Sidebar'a ekle
st.sidebar.download_button(
    label="📥 Excel Olarak İndir",
    data=excel_data,
    file_name=f"{secilen_fark}_veri.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
#st.subheader("Özet Metrikler")

if "Yoğunluk" in secilen_fark:
    harita_aciklama = "Nüfus Yoğunluğu (kişi/km²) Değişimi"
else:
    harita_aciklama = "Toplam Nüfus Sayısı Değişimi (kişi)"

harita_baslik = f"{secilen_fark.replace('_', '–')} Türkiye Haritası<br><sup>{harita_aciklama}</sup>"

st.subheader("🔝 En Fazla Artan ve Azalan 5 İl")

top5_artan = df.sort_values(by=secilen_fark, ascending=False).head(5)[["İl", secilen_fark]]
top5_azalan = df.sort_values(by=secilen_fark).head(5)[["İl", secilen_fark]]

col3, col4 = st.columns(2)

with col3:
    st.markdown("**📈 En Fazla Artan İller**")
    st.dataframe(top5_artan.set_index("İl").style.format("{:,.0f}"))

with col4:
    st.markdown("**📉 En Fazla Azalan İller**")
    st.dataframe(top5_azalan.set_index("İl").style.format("{:,.0f}"))

fig = px.choropleth(
    df,
    geojson=turkey_geo,
    locations="plaka",
    featureidkey="properties.number",
    color=secilen_fark,
    hover_data={"İl": True, secilen_fark: True},
    color_continuous_scale="Turbo",
    range_color=[-100000, 100000],
    title=harita_baslik
)

fig.update_traces(
    hovertemplate=
    "<b>%{customdata[0]}</b><br>" +
    "<span style='font-size:14px'><b>Değişim: %{customdata[1]:,.0f}</b></span><extra></extra>"
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧭 3D Nüfus Yoğunluğu Haritası")

secilen_yil_3d = st.sidebar.selectbox("3D Harita için Yıl Seçiniz (Yoğunluk)", ["2019", "2020", "2021", "2022", "2023"])
yoğunluk_kolon = f"Yoğunluk_{secilen_yil_3d}"

# Eksiksiz verilerle çalış
df_3d = df.dropna(subset=["lat", "lon", yoğunluk_kolon])
df_3d[yoğunluk_kolon] = df_3d[yoğunluk_kolon].astype(float)

# 3D Harita katmanı
layer = pdk.Layer(
    "ColumnLayer",
    data=df_3d,
    get_position='[lon, lat]',
    get_elevation=yoğunluk_kolon,
    elevation_scale=20,
    radius=20000,
    get_fill_color='[255, 105, 180, 160]',  # Canlı pembe ton
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=39.0,
    longitude=35.0,
    zoom=5,
    pitch=50,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "{İl}\nNüfus Yoğunluğu (kişi/km²) Değişimi: {" + yoğunluk_kolon + "}"}
)

st.pydeck_chart(deck)

