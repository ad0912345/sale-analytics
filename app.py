import streamlit as st
import pandas as pd

st.set_page_config(
page_title="11.11 Sale Analytics",
page_icon="🛒",
layout="wide"
)

st.title("🛒 11.11 Sale Analytics Dashboard")
st.caption("Big Data Analytics | Manila Online Seller")

@st.cache_data
def load_data():
revenue = pd.read_csv("results/revenue_by_category.csv")
hourly = pd.read_csv("results/orders_by_hour.csv")
region = pd.read_csv("results/region_summary.csv")
cancellation = pd.read_csv("results/cancellation_by_payment.csv")
aov = pd.read_csv("results/aov_summary.csv")
return revenue, hourly, region, cancellation, aov

try:
revenue, hourly, region, cancellation, aov = load_data()
except Exception as e:
st.error("Unable to load results CSV files.")
st.code(str(e))
st.stop()

def find_col(df, candidates):
columns = {str(c).strip().lower(): c for c in df.columns}
for candidate in candidates:
if candidate.lower() in columns:
return columns[candidate.lower()]
return None

def format_peso(value):
return f"₱{float(value):,.2f}"

category_col = find_col(revenue, ["category", "product_category"])
revenue_col = find_col(
revenue, ["revenue", "total_revenue", "delivered_revenue"]
)
hour_col = find_col(hourly, ["hour", "order_hour"])
hour_count_col = find_col(
hourly, ["order_count", "total_orders", "orders", "count"]
)
region_col = find_col(region, ["region", "region_name"])
region_revenue_col = find_col(
region, ["revenue", "total_revenue", "delivered_revenue"]
)
region_count_col = find_col(
region, ["order_count", "total_orders", "orders", "count"]
)
payment_col = find_col(
cancellation, ["payment_method", "payment", "method"]
)
cancel_rate_col = find_col(
cancellation, ["cancellation_rate", "cancel_rate", "rate"]
)
aov_col = find_col(
aov, ["aov", "average_order_value", "avg_order_value"]
)

required = [
(revenue, [category_col, revenue_col]),
(hourly, [hour_col, hour_count_col]),
(region, [region_col, region_revenue_col, region_count_col]),
(cancellation, [payment_col, cancel_rate_col]),
(aov, [aov_col])
]

for dataframe, columns in required:
if any(column is None for column in columns):
st.error("A required column is missing from a results CSV.")
st.write("Available columns:", dataframe.columns.tolist())
st.stop()

revenue[revenue_col] = pd.to_numeric(
revenue[revenue_col], errors="coerce"
).fillna(0)

hourly[hour_col] = pd.to_numeric(
hourly[hour_col], errors="coerce"
)
hourly[hour_count_col] = pd.to_numeric(
hourly[hour_count_col], errors="coerce"
).fillna(0)

region[region_revenue_col] = pd.to_numeric(
region[region_revenue_col], errors="coerce"
).fillna(0)
region[region_count_col] = pd.to_numeric(
region[region_count_col], errors="coerce"
).fillna(0)

total_revenue = revenue[revenue_col].sum()
total_orders = region[region_count_col].sum()

aov_values = pd.to_numeric(
aov[aov_col], errors="coerce"
).dropna()

average_order_value = (
float(aov_values.iloc[0]) if not aov_values.empty else 0
)

overall_cancellation_rate = None

if (
"cancelled_orders" in cancellation.columns
and "total_orders" in cancellation.columns
):
cancelled = pd.to_numeric(
cancellation["cancelled_orders"], errors="coerce"
).fillna(0).sum()
payment_total = pd.to_numeric(
cancellation["total_orders"], errors="coerce"
).fillna(0).sum()

```
if payment_total > 0:
    overall_cancellation_rate = cancelled / payment_total * 100
```

elif (
"cancelled_count" in cancellation.columns
and "total_count" in cancellation.columns
):
cancelled = pd.to_numeric(
cancellation["cancelled_count"], errors="coerce"
).fillna(0).sum()
payment_total = pd.to_numeric(
cancellation["total_count"], errors="coerce"
).fillna(0).sum()

```
if payment_total > 0:
    overall_cancellation_rate = cancelled / payment_total * 100
```

if overall_cancellation_rate is None:
rates = pd.to_numeric(
cancellation[cancel_rate_col], errors="coerce"
).dropna()

```
if not rates.empty:
    if rates.max() <= 1:
        overall_cancellation_rate = rates.mean() * 100
    else:
        overall_cancellation_rate = rates.mean()
```

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Delivered Revenue", format_peso(total_revenue))
kpi2.metric("Total Orders", f"{total_orders:,.0f}")
kpi3.metric(
"Cancellation Rate",
(
f"{overall_cancellation_rate:.2f}%"
if overall_cancellation_rate is not None
else "N/A"
)
)
kpi4.metric("Average Order Value", format_peso(average_order_value))

st.divider()

st.subheader("📦 Revenue by Category")

revenue_chart = revenue.sort_values(revenue_col, ascending=False)
st.bar_chart(revenue_chart.set_index(category_col)[revenue_col])

with st.expander("View revenue data"):
st.dataframe(revenue_chart, use_container_width=True)

st.subheader("🕒 Orders by Hour")

hourly_chart = hourly.dropna(subset=[hour_col]).copy()
hourly_chart = hourly_chart.sort_values(hour_col)
hourly_chart["Hour"] = hourly_chart[hour_col].astype(int).map(
lambda hour: f"{hour:02d}:00"
)

st.line_chart(hourly_chart.set_index("Hour")[hour_count_col])

with st.expander("View hourly order data"):
st.dataframe(hourly_chart, use_container_width=True)

st.subheader("📍 Regional Sales Analysis")

region_names = sorted(
region[region_col].dropna().astype(str).unique().tolist()
)

selected_region = st.selectbox(
"Filter by region",
["All Regions"] + region_names
)

region_view = region.copy()

if selected_region != "All Regions":
region_view = region_view[
region_view[region_col].astype(str) == selected_region
]

st.dataframe(region_view, use_container_width=True)

region_kpi1, region_kpi2 = st.columns(2)

region_kpi1.metric(
"Selected Region Revenue",
format_peso(region_view[region_revenue_col].sum())
)

region_kpi2.metric(
"Selected Region Orders",
f"{region_view[region_count_col].sum():,.0f}"
)

st.subheader("💳 Cancellation Rate by Payment Method")
st.dataframe(cancellation, use_container_width=True)

st.divider()

st.caption(
"11.11 Sale Analytics | Big Data Analytics Project"
)
