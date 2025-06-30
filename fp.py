import streamlit as st
import pandas as pd
import plotly.express as px

# Title and Sidebar Setup
st.set_page_config(page_title="Financial Performance Dashboard", layout="wide")
st.title("📊 Financial Performance Dashboard")

# Upload Dataset
df = st.file_uploader("Upload Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if df:
    if df.name.endswith(".csv"):
        data = pd.read_csv(df)
    else:
        data = pd.read_excel(df)

    # Date Handling
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data['Year'] = pd.DatetimeIndex(data['Date']).year
    data['Month Name'] = pd.DatetimeIndex(data['Date']).month_name()

    # Calculated Fields
    data['Profit Margin'] = data['Profit'] / data['Sales']
    data['Total Discounts'] = data['Discounts']
    data['Total Revenue'] = data['Gross Sales']
    data['COGS to Sales'] = data['COGS'] / data['Sales']
    data['Net Sales'] = data['Gross Sales'] - data['Discounts']

    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_segment = st.sidebar.multiselect("Segment", options=data['Segment'].unique(), default=data['Segment'].unique())
    selected_country = st.sidebar.multiselect("Country", options=data['Country'].unique(), default=data['Country'].unique())
    selected_year = st.sidebar.multiselect("Year", options=data['Year'].unique(), default=data['Year'].unique())

    filtered_data = data[
        (data['Segment'].isin(selected_segment)) &
        (data['Country'].isin(selected_country)) &
        (data['Year'].isin(selected_year))
    ]

    # KPI Section
    total_sales = filtered_data['Sales'].sum()
    total_profit = filtered_data['Profit'].sum()
    total_cogs = filtered_data['COGS'].sum()
    total_discount = filtered_data['Discounts'].sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Sales", f"${total_sales:,.0f}")
    kpi2.metric("Total Profit", f"${total_profit:,.0f}")
    kpi3.metric("Total COGS", f"${total_cogs:,.0f}")
    kpi4.metric("Total Discounts", f"${total_discount:,.0f}")

    st.markdown("---")

    # Visuals
    tab1, tab2, tab3, tab4 = st.tabs(["Sales by Country", "Trend Over Time", "Gross vs Discount", "Product Discounts"])

    with tab1:
        chart_data = filtered_data.groupby('Country').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        fig = px.bar(chart_data, x='Country', y='Sales', color='Profit', title="Sales and Profit by Country")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        trend_data = filtered_data.groupby(['Year', 'Month Name']).agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        fig = px.line(trend_data, x='Month Name', y='Sales', color='Year', title="Sales Trend Over Time")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.scatter(filtered_data, x='Gross Sales', y='Discounts', color='Country', title="Gross Sales vs Discounts")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        heatmap_data = filtered_data.groupby(['Product', 'Discount Band']).agg({'Sales': 'sum'}).reset_index()
        fig = px.density_heatmap(heatmap_data, x='Discount Band', y='Product', z='Sales', color_continuous_scale='Blues', title="Sales by Product and Discount Band")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload the dataset to get started.")
