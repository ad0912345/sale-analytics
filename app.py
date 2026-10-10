```python
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
    st.error("Hindi ma-load ang results CSV files.")
    st.code(str(e))
    st.stop()


def find_column(data, candidates):
    """Find a column using possible column-name variations."""
    for candidate in candidates:
        for column in data.columns:
            if column.strip().lower() == candidate.lower():
                return column
    return None


def format_peso(value):
    try:
        return f"₱{float(value):,.2f}"
    except (ValueError, TypeError):
        return "₱0.00"


def format_number(value):
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return "0"

category_col = find_column(
    revenue, ["category", "product_category"]
)
category_revenue_col = find_column(
    revenue, ["revenue", "total_revenue", "delivered_revenue"]
)

hour_col = find_column(
    hourly, ["hour", "order_hour"]
)
hour_orders_col = find_column(
    hourly, ["order_count", "total_orders", "orders", "count"]
)

region_col = find_column(
    region, ["region", "region_name"]
)
region_revenue_col = find_column(
    region, ["revenue", "total_revenue", "delivered_revenue"]
)
region_orders_col = find_column(
    region, ["order_count", "total_orders", "orders", "count"]
)

payment_col = find_column(
    cancellation, ["payment_method", "payment", "method"]
)
cancel_rate_col = find_column(
    cancellation, ["cancellation_rate", "cancel_rate", "rate"]
)

aov_col = find_column(
    aov, ["aov", "average_order_value", "avg_order_value"]
)

required_columns = [
    ("Revenue by category", revenue, category_col, category_revenue_col),
    ("Orders by hour", hourly, hour_col, hour_orders_col),
    ("Region summary", region, region_col, region_revenue_col),
    ("Region order count", region, region_col, region_orders_col),
    ("Cancellation summary", cancellation, payment_col, cancel_rate_col),
    ("AOV summary", aov, aov_col),
]

for item in required_columns:
    name, *columns = item
    if any(column is None for column in columns):
        st.error(f"May nawawalang column sa {name} CSV.")
        st.write("Available columns:", (
            revenue.columns.tolist()
            if name == "Revenue by category"
            else hourly.columns.tolist()
            if name == "Orders by hour"
            else region.columns.tolist()
            if name in ["Region summary", "Region order count"]
            else cancellation.columns.tolist()
            if name == "Cancellation summary"
            else aov.columns.tolist()
        ))
        st.stop()


total_revenue = pd.to_numeric(
    revenue[category_revenue_col], errors="coerce"
).fillna(0).sum()

total_orders = (
    pd.to_numeric(region[region_orders_col], errors="coerce")
    .fillna(0)
    .sum()
)

total_cancellations = None

if (
    "cancelled_orders" in cancellation.columns
    and "total_orders" in cancellation.columns
):
    cancelled = pd.to_numeric(
        cancellation["cancelled_orders"], errors="coerce"
    ).fillna(0).sum()

    payment_orders = pd.to_numeric(
        cancellation["total_orders"], errors="coerce"
    ).fillna(0).sum()

    if payment_orders > 0:
        total_cancellations = cancelled / payment_orders * 100

elif (
    "cancelled_count" in cancellation.columns
    and "total_count" in cancellation.columns
):
    cancelled = pd.to_numeric(
        cancellation["cancelled_count"], errors="coerce"
    ).fillna(0).sum()

    payment_orders = pd.to_numeric(
        cancellation["total_count"], errors="coerce"
    ).fillna(0).sum()

    if payment_orders > 0:
        total_cancellations = cancelled / payment_orders * 100

if total_cancellations is None:
    rates = pd.to_numeric(
        cancellation[cancel_rate_col], errors="coerce"
    ).dropna()

    if not rates.empty:
        if rates.max() <= 1:
            total_cancellations = rates.mean() * 100
        else:
            total_cancellations = rates.mean()

aov_values = pd.to_numeric(aov[aov_col], errors="coerce").dropna()
average_order_value = (
    aov_values.iloc[0] if not aov_values.empty else 0
)


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Delivered Revenue",
    format_peso(total_revenue)
)

col2.metric(
    "Total Orders",
    format_number(total_orders)
)

col3.metric(
    "Cancellation Rate",
    f"{total_cancellations:.2f}%"
    if total_cancellations is not None
    else "N/A"
)

col4.metric(
    "Average Order Value",
    format_peso(average_order_value)
)

st.divider()



st.subheader("📦 Revenue by Category")

revenue_chart = revenue.copy()
revenue_chart[category_revenue_col] = pd.to_numeric(
    revenue_chart[category_revenue_col], errors="coerce"
).fillna(0)

revenue_chart = revenue_chart.sort_values(
    category_revenue_col, ascending=False
)

st.bar_chart(
    revenue_chart.set_index(category_col)[category_revenue_col]
)

with st.expander("View revenue data"):
    st.dataframe(revenue_chart, use_container_width=True)


st.subheader("🕒 Orders by Hour")

hourly_chart = hourly.copy()
hourly_chart[hour_col] = pd.to_numeric(
    hourly_chart[hour_col], errors="coerce"
)
hourly_chart[hour_orders_col] = pd.to_numeric(
    hourly_chart[hour_orders_col], errors="coerce"
).fillna(0)

hourly_chart = hourly_chart.dropna(subset=[hour_col])
hourly_chart = hourly_chart.sort_values(hour_col)
hourly_chart["Hour"] = hourly_chart[hour_col].astype(int).map(
    lambda hour: f"{hour:02d}:00"
)

st.line_chart(
    hourly_chart.set_index("Hour")[hour_orders_col]
)

with st.expander("View hourly order data"):
    st.dataframe(hourly_chart, use_container_width=True)



st.subheader("📍 Regional Sales Analysis")

regions = sorted(
    region[region_col].dropna().astype(str).unique().tolist()
)

selected_region = st.selectbox(
    "Filter by region",
    ["All Regions"] + regions
)

region_view = region.copy()

if selected_region != "All Regions":
    region_view = region_view[
        region_view[region_col].astype(str) == selected_region
    ]

region_view[region_revenue_col] = pd.to_numeric(
    region_view[region_revenue_col], errors="coerce"
).fillna(0)

region_view[region_orders_col] = pd.to_numeric(
    region_view[region_orders_col], errors="coerce"
).fillna(0)

st.dataframe(region_view, use_container_width=True)

if not region_view.empty:
    selected_revenue = region_view[region_revenue_col].sum()
    selected_orders = region_view[region_orders_col].sum()

    rcol1, rcol2 = st.columns(2)
    rcol1.metric("Selected Region Revenue", format_peso(selected_revenue))
    rcol2.metric("Selected Region Orders", format_number(selected_orders))



st.subheader("💳 Cancellation Rate by Payment Method")

cancel_view = cancellation.copy()
st.dataframe(cancel_view, use_container_width=True)

st.divider()


st.subheader("🤖 AI Sales Briefing")

st.write(
    "Gumawa ng maikling sales briefing gamit ang summary data "
    "at isang rekomendasyon para sa susunod na 11.11 sale."
)

if st.button("Generate AI Briefing", type="primary"):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:
            st.error(
                "Walang GEMINI_API_KEY sa Streamlit Secrets. "
                "Idagdag ito sa App Settings → Secrets."
            )
            st.stop()

        client = genai.Client(api_key=api_key)


        prompt = f"""
You are a business data analyst for a Manila online seller's 11.11 sale.

Use ONLY the summary data below. Do not invent facts or numbers.
If a detail is unavailable, say it is unavailable.

Delivered revenue by category:
{revenue.to_string(index=False)}

Orders by hour:
{hourly.to_string(index=False)}

Regional summary:
{region.to_string(index=False)}

Cancellation rate by payment method:
{cancellation.to_string(index=False)}

Average order value summary:
{aov.to_string(index=False)}

Write exactly 5 sentences:
1. Summarize overall sales performance.
2. Identify the strongest product category if supported by the data.
3. Describe the order-hour pattern if supported by the data.
4. Mention a regional or payment-method insight if supported by the data.
5. Give ONE specific, actionable recommendation for next year's 11.11 sale.

Keep the language clear, concise, and suitable for a store owner.
Do not claim correlation or causation unless the data supports it.
"""

        with st.spinner("Generating AI briefing..."):
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

        if response.text:
            st.success("AI briefing generated!")
            st.write(response.text)
        else:
            st.warning(
                "Walang text na naibalik ang AI. Subukan ulit."
            )

    except Exception as e:
        st.error("Hindi nagawa ang AI briefing.")
        st.write("Error type:", type(e).__name__)
        st.code(str(e))



st.divider()
st.caption(
    "11.11 Sale Analytics | Big Data Analytics Project | "
    "Dashboard uses aggregated CSV summaries."
)
```
