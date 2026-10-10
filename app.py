import streamlit as st
import pandas as pd
from google import genai

st.set_page_config(
page_title="11.11 Sale Analytics",
page_icon="🛒",
layout="wide"
)

st.title("🛒 11.11 Sale Analytics Dashboard")
st.caption("Big Data Analytics | Manila Online Seller")

# LOAD CSV SUMMARY FILES

@st.cache_data
def load_data():
revenue = pd.read_csv("results/revenue_by_category.csv")
hourly = pd.read_csv("results/orders_by_hour.csv")
region = pd.read_csv("results/region_summary.csv")
cancellation = pd.read_csv("results/cancellation_by_payment.csv")
aov = pd.read_csv("results/aov_summary.csv")

```
return revenue, hourly, region, cancellation, aov
```

try:
revenue, hourly, region, cancellation, aov = load_data()
except Exception as e:
st.error("Hindi ma-load ang results CSV files.")
st.code(str(e))
st.stop()

# FIND COLUMN NAMES AUTOMATICALLY

def find_col(df, possible_names):
lookup = {str(c).strip().lower(): c for c in df.columns}

```
for name in possible_names:
    if name.lower() in lookup:
        return lookup[name.lower()]

return None
```

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

# CHECK REQUIRED COLUMNS

required = {
"Revenue by category": (revenue, [category_col, revenue_col]),
"Orders by hour": (hourly, [hour_col, hour_count_col]),
"Region summary": (
region, [region_col, region_revenue_col, region_count_col]
),
"Cancellation by payment": (
cancellation, [payment_col, cancel_rate_col]
),
"AOV summary": (aov, [aov_col])
}

for name, (df, columns) in required.items():
if any(col is None for col in columns):
st.error(f"May kulang o hindi tugmang column sa {name}.")
st.write("Available columns:", df.columns.tolist())
st.stop()

# CONVERT NUMERIC VALUES

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

# KPI CALCULATIONS

total_revenue = revenue[revenue_col].sum()
total_orders = region[region_count_col].sum()

aov_values = pd.to_numeric(aov[aov_col], errors="coerce").dropna()
average_order_value = (
float(aov_values.iloc[0]) if not aov_values.empty else 0
)

# Compute a weighted overall cancellation rate when counts are available.

total_cancellation_rate = None

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
    total_cancellation_rate = cancelled / payment_total * 100
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
    total_cancellation_rate = cancelled / payment_total * 100
```

if total_cancellation_rate is None:
rates = pd.to_numeric(
cancellation[cancel_rate_col], errors="coerce"
).dropna()

```
if not rates.empty:
    if rates.max() <= 1:
        total_cancellation_rate = rates.mean() * 100
    else:
        total_cancellation_rate = rates.mean()
```

# KPI CARDS

def peso(value):
return f"₱{value:,.2f}"

col1, col2, col3, col4 = st.columns(4)

col1.metric("Delivered Revenue", peso(total_revenue))
col2.metric("Total Orders", f"{total_orders:,.0f}")
col3.metric(
"Cancellation Rate",
f"{total_cancellation_rate:.2f}%"
if total_cancellation_rate is not None
else "N/A"
)
col4.metric("Average Order Value", peso(average_order_value))

st.divider()

# REVENUE BY CATEGORY

st.subheader("📦 Revenue by Category")

revenue_chart = revenue.sort_values(revenue_col, ascending=False)

st.bar_chart(
revenue_chart.set_index(category_col)[revenue_col]
)

with st.expander("View revenue data"):
st.dataframe(revenue_chart, use_container_width=True)

# ORDERS BY HOUR

st.subheader("🕒 Orders by Hour")

hourly_chart = hourly.dropna(subset=[hour_col]).copy()
hourly_chart = hourly_chart.sort_values(hour_col)
hourly_chart["Hour"] = hourly_chart[hour_col].astype(int).map(
lambda h: f"{h:02d}:00"
)

st.line_chart(
hourly_chart.set_index("Hour")[hour_count_col]
)

with st.expander("View hourly data"):
st.dataframe(hourly_chart, use_container_width=True)

# REGION FILTER

st.subheader("📍 Regional Sales Analysis")

region_names = sorted(
region[region_col].dropna().astype(str).unique().tolist()
)

selected_region = st.selectbox(
"Select region",
["All Regions"] + region_names
)

region_view = region.copy()

if selected_region != "All Regions":
region_view = region_view[
region_view[region_col].astype(str) == selected_region
]

st.dataframe(region_view, use_container_width=True)

region_revenue_total = region_view[region_revenue_col].sum()
region_order_total = region_view[region_count_col].sum()

rcol1, rcol2 = st.columns(2)
rcol1.metric("Selected Region Revenue", peso(region_revenue_total))
rcol2.metric("Selected Region Orders", f"{region_order_total:,.0f}")

# CANCELLATION BY PAYMENT METHOD

st.subheader("💳 Cancellation Rate by Payment Method")
st.dataframe(cancellation, use_container_width=True)

st.divider()

# GEMINI AI BRIEFING

st.subheader("🤖 AI Sales Briefing")

st.write(
"Gumawa ng limang pangungusap na briefing tungkol sa sales "
"at isang rekomendasyon para sa susunod na 11.11 sale."
)

if st.button("Generate AI Briefing", type="primary"):
try:
api_key = st.secrets.get("GEMINI_API_KEY", "")

```
    if not api_key:
        st.error(
            "Walang GEMINI_API_KEY sa Streamlit Secrets. "
            "Idagdag ito sa App Settings → Secrets."
        )
    else:
        client = genai.Client(api_key=api_key)

        prompt = f"""
```

You are a business data analyst for a Manila online seller's 11.11 sale.

Use only the summary data below. Do not invent facts or numbers.
If information is unavailable, say so.

Delivered revenue by category:
{revenue.to_string(index=False)}

Orders by hour:
{hourly.to_string(index=False)}

Regional summary:
{region.to_string(index=False)}

Cancellation by payment method:
{cancellation.to_string(index=False)}

Average order value:
{aov.to_string(index=False)}

Write exactly 5 sentences:

1. Summarize sales performance.
2. Identify the strongest category if supported by the data.
3. Describe the hourly order pattern if supported by the data.
4. Mention a regional or payment-method insight if supported by the data.
5. Give one specific, actionable recommendation for next year's sale.

Be concise and suitable for a store owner.
Do not invent values or unsupported conclusions.
"""

```
        with st.spinner("Generating AI briefing..."):
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

        if response.text:
            st.success("AI briefing generated!")
            st.write(response.text)
        else:
            st.warning("Walang text na naibalik ng AI. Subukan ulit.")

except Exception as e:
    st.error("Hindi nagawa ang AI briefing.")
    st.write("Error type:", type(e).__name__)
    st.code(str(e))
```

# FOOTER

st.divider()
st.caption(
"11.11 Sale Analytics | Big Data Analytics Project | "
"Dashboard uses aggregated CSV summary files."
)
