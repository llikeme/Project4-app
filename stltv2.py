import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
import streamlit.components.v1 as components


today = datetime.today().date()

# 设置页面宽度
#st.set_page_config(layout="wide")
st.title("Food Price Tracker")
st.subheader("📊 1. Current Food Prices by City, Store, and Category")

# 读取价格数据
df_prices = pd.read_csv("price_series_with_diff.csv", parse_dates=["date"])
df_cpi = pd.read_csv("df_cpi.csv", parse_dates=["date"])
df_news = pd.read_csv("df_news.csv", parse_dates=["date"])

# 日期选择器（默认今天）
today = datetime.today().date()
selected_date = st.date_input("📅 Select Date", today)

# 获取筛选选项
cities = df_prices["city"].unique().tolist()
stores = sorted(df_prices["store"].unique().tolist())  # 只保留实际门店
categories = df_prices["category"].unique().tolist()

# 多选：城市和品类
selected_cities = st.multiselect("🏙️ Select Cities", cities, default=cities)
selected_store = st.selectbox("🏬 Select Store (Choose One)", stores)  # 强制单选
selected_categories = st.multiselect("🍽️ Select Categories", categories, default=categories)

# 筛选数据
filtered = df_prices[
    (df_prices["date"] == pd.to_datetime(selected_date)) &
    (df_prices["city"].isin(selected_cities)) &
    (df_prices["store"] == selected_store) &
    (df_prices["category"].isin(selected_categories))
]

# 展示图表
if not filtered.empty:
    st.subheader("📉 Average Price by City and Category")
    fig_avg = px.bar(
        filtered,
        x="category",
        y="avg_price",
        color="city",
        barmode="group",
        title="Average Price (Grouped by City)",
        labels={"avg_price": "Average Price (NZD)", "category": "Category"}
    )
    st.plotly_chart(fig_avg)

    st.subheader("📉 Minimum Price by City and Category")
    fig_min = px.bar(
        filtered,
        x="category",
        y="min_price",
        color="city",
        barmode="group",
        title="Minimum Price (Grouped by City)",
        labels={"min_price": "Minimum Price (NZD)", "category": "Category"}
    )
    st.plotly_chart(fig_min)
else:
    st.warning("No data available for the selected filters and date.")





# extend

# ✅ Treemap 图示：按城市和类别展示价格总额
st.subheader("🗺️ 2. Treemap of Food Prices by City and Category")

date_selected = st.date_input("📅 Select date", today)
# 筛选选定日期的数据
df_latest = df_prices[df_prices["date"] == pd.to_datetime(date_selected)]

if not df_latest.empty:
    # 用 avg_price 作为总额值（也可以改为 min_price）
    df_latest["total_value"] = df_latest["avg_price"]

    fig_treemap = px.treemap(
        df_latest,
        path=["city", "category"],
        values="total_value",
        color="diff_pct_avg",  # 颜色表示价格涨跌
        color_continuous_scale="RdBu",
        title=f"Treemap of Average Food Prices on {date_selected}"
    )
    st.plotly_chart(fig_treemap, use_container_width=True)
else:
    st.write("No data available for the selected date.")



# extend 2
st.subheader("📈 3. 7-Day or 30-Day Food Price Trends Across Cities")

# 价格类型选项映射
price_display_map = {
    "Average Price": "avg_price",
    "Minimum Price": "min_price"
}
selected_price_label = st.radio("💲 Select Price Type", list(price_display_map.keys()), horizontal=True)
price_type = price_display_map[selected_price_label]

# 周期选择
trend_days = st.radio("🕒 Select Trend Period", [7, 30], horizontal=True)

# 设置分析对象
products = ["beef", "bread", "butter", "egg", "milk"]
cities = ["Auckland", "Christchurch", "Wellington"]

# 时间筛选
end_date = df_prices["date"].max()
start_date = end_date - timedelta(days=trend_days - 1)
filtered = df_prices[
    (df_prices["date"] >= start_date) &
    (df_prices["date"] <= end_date) &
    (df_prices["category"].isin(products)) &
    (df_prices["city"].isin(cities))
]

# 每个城市一个趋势图
for city in cities:
    st.subheader(f"📍 {city} - {trend_days}-Day Trend ({selected_price_label})")

    fig = go.Figure()
    city_data = filtered[filtered["city"] == city]

    for product in products:
        prod_data = city_data[city_data["category"] == product]
        # 聚合每日平均价格
        daily_avg = prod_data.groupby("date")[price_type].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=daily_avg["date"],
            y=daily_avg[price_type],
            mode="lines+markers",
            name=product
        ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (NZD)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


# extend 3
# CPI 折线图（历史 + 预测 + 区间）
st.subheader("📉 4. Micro-CPI Trend and Forecast")
fig_cpi = go.Figure()

# 历史 CPI
hist = df_cpi[df_cpi["micro_cpi"].notna()]
fig_cpi.add_trace(go.Scatter(
    x=hist["date"], y=hist["micro_cpi"],
    mode="lines+markers",
    name="Historical CPI"
))

# 预测 CPI
pred = df_cpi[df_cpi["forecast"].notna()]
fig_cpi.add_trace(go.Scatter(
    x=pred["date"], y=pred["forecast"],
    mode="lines+markers",
    name="Forecast CPI",
    line=dict(dash="dash")
))

# 区间填充
fig_cpi.add_trace(go.Scatter(
    x=pd.concat([pred["date"], pred["date"][::-1]]),
    y=pd.concat([pred["forecast_upper"], pred["forecast_lower"][::-1]]),
    fill='toself',
    fillcolor='rgba(0,100,80,0.2)',
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo="skip",
    showlegend=True,
    name="Forecast Range"
))

fig_cpi.update_layout(
    yaxis=dict(
        title="Micro-CPI",
        range=[1280, 1320]  # ✅ 指定 Y 轴的上下限
    ),
    xaxis_title="Date",
    title="Micro-CPI: Historical + Forecast"
)

st.plotly_chart(fig_cpi)

# 新闻轮播模块（每5秒刷新）
# ✅ 新闻滚动模块（HTML + CSS + 启用 unsafe_allow_html）
st.subheader("📰 Relevant News")
# 获取前5条新闻
news_to_display = df_news[df_news["date"] <= pd.to_datetime(date_selected)].sort_values("date", ascending=False).head(5)
news_items = ""
for i, (_, row) in enumerate(news_to_display.iterrows()):
    delay = i * 6  # 每条新闻延迟6秒播出
    news_items += f"""
    <div class="news-item" style="animation-delay: {delay}s;">
        <b>📰 {row['title']} — <i>{row['source']}</i></b>
    </div>
    """

# 完整 CSS + 动画控制（解决重叠）
news_to_display = df_news[df_news["date"] <= pd.to_datetime(date_selected)] \
    .sort_values("date", ascending=False).head(5)

# 每条新闻显示在哪个“时间窗口”
N = len(news_to_display)
news_items = ""
for i, (_, row) in enumerate(news_to_display.iterrows()):
    start_percent = int((i / N) * 100)
    end_percent = int(((i + 1) / N) * 100)
    news_items += f"""
    <div class="news-item item-{i}">
        <a href=\"{row['link']}\" target=\"_blank\">
        <b>📰 {row['title']} — <i>{row['source']}</i></b>
    </div>
    """

# 每个 item 的 keyframes 在不同百分比范围显示
keyframes = ""
for i in range(N):
    start = int((i / N) * 100)
    fadein = start + 5
    hold = start + 15
    end = int(((i + 1) / N) * 100)

    keyframes += f"""
    .item-{i} {{
        animation: show-item-{i} {N * 6}s linear infinite;
    }}

    @keyframes show-item-{i} {{
        0% {{ opacity: 0; visibility: hidden; transform: translateY(20px); }}
        {start}% {{ opacity: 0; visibility: hidden; transform: translateY(20px); }}
        {fadein}% {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        {hold}% {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        {end}% {{ opacity: 0; visibility: hidden; transform: translateY(-20px); }}
        100% {{ opacity: 0; visibility: hidden; transform: translateY(-20px); }}
    }}
    """

html_code = f"""
<style>
.scrolling-box {{
    position: relative;
    height: 50px;
    overflow: hidden;
    background: #f7f7f7;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding-left: 10px;
    font-size: 16px;  
}}

.news-item {{
    position: absolute;
    width: 100%;
    height: 50px;
    line-height: 50px;
    opacity: 0;
    visibility: hidden;
    animation-fill-mode: both;
}}

{keyframes}
</style>

<div class="scrolling-box">
    {news_items}
</div>
"""

components.html(html_code, height=60)


# 更新时间显示
st.markdown("🔁 Last updated: " + datetime.now().strftime("%Y-%m-%d"))

