import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")
st.title("📈 Financial Performance Dashboard")

# --------------------------- #
# 📂 FILE UPLOAD SECTION
# --------------------------- #
df = st.file_uploader("📤 Upload your Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if df:
    data = pd.read_csv(df) if df.name.endswith(".csv") else pd.read_excel(df)

    # Clean and rename columns
    data.columns = data.columns.str.strip()
    column_renames = {
        ' Product ': 'Product', ' Discount Band ': 'Discount Band', ' Units Sold ': 'Units Sold',
        ' Manufacturing Price ': 'Manufacturing Price', ' Sale Price ': 'Sale Price',
        ' Gross Sales ': 'Gross Sales', ' Discounts ': 'Discounts', '  Sales ': 'Sales',
        ' COGS ': 'COGS', ' Profit ': 'Profit', ' Month Name ': 'Month Name'
    }
    data.rename(columns=column_renames, inplace=True)

    currency_columns = ['Units Sold', 'Manufacturing Price', 'Sale Price',
                        'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit']
    for col in currency_columns:
        if col in data.columns:
            data[col] = data[col].replace('[\$,]', '', regex=True).replace('-', '0')
            data[col] = pd.to_numeric(data[col], errors='coerce')

    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Year'] = data['Date'].dt.year
        data['Month Name'] = data['Date'].dt.month_name()

    if {'Profit', 'Sales'}.issubset(data.columns):
        data['Profit Margin'] = data['Profit'].div(data['Sales'].replace(0, pd.NA))
    if {'COGS', 'Sales'}.issubset(data.columns):
        data['COGS to Sales'] = data['COGS'].div(data['Sales'].replace(0, pd.NA))
    if {'Gross Sales', 'Discounts'}.issubset(data.columns):
        data['Net Sales'] = data['Gross Sales'] - data['Discounts']
    if 'Sales' in data.columns:
        data['Cumulative Sales'] = data['Sales'].cumsum()

    # Filters
    st.sidebar.header("🔍 Filter Data")
    segment_filter = st.sidebar.multiselect("Segment", data['Segment'].dropna().unique() if 'Segment' in data.columns else [], default=None)
    country_filter = st.sidebar.multiselect("Country", data['Country'].dropna().unique() if 'Country' in data.columns else [], default=None)
    year_filter = st.sidebar.multiselect("Year", data['Year'].dropna().unique() if 'Year' in data.columns else [], default=None)

    filtered_data = data.copy()
    if segment_filter and 'Segment' in data.columns:
        filtered_data = filtered_data[filtered_data['Segment'].isin(segment_filter)]
    if country_filter and 'Country' in data.columns:
        filtered_data = filtered_data[filtered_data['Country'].isin(country_filter)]
    if year_filter and 'Year' in data.columns:
        filtered_data = filtered_data[filtered_data['Year'].isin(year_filter)]

    # KPIs
    st.markdown("## 📌 Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Sales", f"${filtered_data['Sales'].sum():,.0f}" if 'Sales' in filtered_data.columns else "N/A")
    kpi2.metric("Total Profit", f"${filtered_data['Profit'].sum():,.0f}" if 'Profit' in filtered_data.columns else "N/A")
    kpi3.metric("Total COGS", f"${filtered_data['COGS'].sum():,.0f}" if 'COGS' in filtered_data.columns else "N/A")
    kpi4.metric("Total Discounts", f"${filtered_data['Discounts'].sum():,.0f}" if 'Discounts' in filtered_data.columns else "N/A")

    st.markdown("---")

    # Visualizations
    st.markdown("### 📊 Financial Visualizations")
    chart_tabs = st.tabs([
        "Line: Sales Trend", "Bar: Sales by Segment", "Pie: Profit by Product",
        "Heatmap: Country vs Segment", "Scatter: Discount vs Profit", "Map: Revenue by Country",
        "Box: Manufacturing Price", "Histogram: Sales Distribution",
        "Stacked Bar: Sales, Discounts, Net", "Area: Cumulative Sales",
        "Dual Axis: Sales vs Profit", "Treemap: Product Sales", "Funnel: Segment Sales",
        "Waterfall: Profit Breakdown"
    ])

    with chart_tabs[0]:
        if {'Date', 'Sales'}.issubset(filtered_data.columns):
            st.plotly_chart(px.line(filtered_data, x='Date', y='Sales', title="Sales Trend Over Time"), use_container_width=True)

    with chart_tabs[1]:
        if {'Segment', 'Sales'}.issubset(filtered_data.columns):
            bar_data = filtered_data.groupby('Segment')['Sales'].sum().reset_index()
            st.plotly_chart(px.bar(bar_data, x='Segment', y='Sales', title="Sales by Segment"), use_container_width=True)

    with chart_tabs[2]:
        if {'Product', 'Profit'}.issubset(filtered_data.columns):
            pie_data = filtered_data.groupby('Product')['Profit'].sum().reset_index()
            st.plotly_chart(px.pie(pie_data, names='Product', values='Profit', title="Profit by Product"), use_container_width=True)

    with chart_tabs[3]:
        if {'Country', 'Segment', 'Sales'}.issubset(filtered_data.columns):
            heat = filtered_data.groupby(['Country', 'Segment'])['Sales'].sum().reset_index()
            st.plotly_chart(px.density_heatmap(heat, x='Segment', y='Country', z='Sales', title="Sales by Country and Segment", color_continuous_scale='Viridis'), use_container_width=True)

    with chart_tabs[4]:
        if {'Discounts', 'Profit'}.issubset(filtered_data.columns):
            st.plotly_chart(px.scatter(filtered_data, x='Discounts', y='Profit', color='Country', title="Discounts vs Profit"), use_container_width=True)

    with chart_tabs[5]:
        if {'Country', 'Sales'}.issubset(filtered_data.columns):
            map_data = filtered_data.groupby('Country')['Sales'].sum().reset_index()
            map_data['Country'] = map_data['Country'].astype(str)
            st.plotly_chart(px.choropleth(map_data, locations="Country", locationmode="country names", color="Sales", title="Sales by Country"), use_container_width=True)

    with chart_tabs[6]:
        if 'Manufacturing Price' in filtered_data.columns:
            st.plotly_chart(px.box(filtered_data, y='Manufacturing Price', title="Manufacturing Price Distribution"), use_container_width=True)

    with chart_tabs[7]:
        if 'Sales' in filtered_data.columns:
            st.plotly_chart(px.histogram(filtered_data, x='Sales', title="Sales Distribution"), use_container_width=True)

    with chart_tabs[8]:
        if {'Gross Sales', 'Discounts', 'Net Sales'}.issubset(filtered_data.columns):
            stacked = filtered_data[['Gross Sales', 'Discounts', 'Net Sales']].sum().reset_index()
            stacked.columns = ['Metric', 'Value']
            st.plotly_chart(px.bar(stacked, x='Metric', y='Value', title="Stacked Financial Metrics"), use_container_width=True)

    with chart_tabs[9]:
        if 'Date' in filtered_data.columns and 'Cumulative Sales' in filtered_data.columns:
            st.plotly_chart(px.area(filtered_data, x='Date', y='Cumulative Sales', title="Cumulative Sales Over Time"), use_container_width=True)

    with chart_tabs[10]:
        if {'Date', 'Sales', 'Profit'}.issubset(filtered_data.columns):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=filtered_data['Date'], y=filtered_data['Sales'], mode='lines', name='Sales'))
            fig.add_trace(go.Scatter(x=filtered_data['Date'], y=filtered_data['Profit'], mode='lines', name='Profit'))
            fig.update_layout(title="Dual Axis: Sales vs Profit")
            st.plotly_chart(fig, use_container_width=True)

    with chart_tabs[11]:
        if {'Product', 'Sales'}.issubset(filtered_data.columns):
            tree = filtered_data.groupby('Product')['Sales'].sum().reset_index()
            st.plotly_chart(px.treemap(tree, path=['Product'], values='Sales', title="Product Sales Treemap"), use_container_width=True)

    with chart_tabs[12]:
        if {'Segment', 'Sales'}.issubset(filtered_data.columns):
            funnel = filtered_data.groupby('Segment')['Sales'].sum().reset_index().sort_values(by='Sales', ascending=False)
            st.plotly_chart(px.funnel(funnel, x='Sales', y='Segment', title="Funnel: Sales by Segment"), use_container_width=True)

    with chart_tabs[13]:
        if {'Product', 'Profit'}.issubset(filtered_data.columns):
            waterfall = filtered_data.groupby('Product')['Profit'].sum().reset_index()
            fig = go.Figure(go.Waterfall(x=waterfall['Product'], y=waterfall['Profit'], measure=['relative']*len(waterfall)))
            fig.update_layout(title="Profit Breakdown by Product")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📂 Please upload a dataset file to begin analyzing.")


         




