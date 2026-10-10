
import streamlit as st
import pandas as pd
import os
from google import genai

st.set_page_config(
    page_title="11.11 Sale Analytics",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ 11.11 Sale Analytics Dashboard")
st.caption("Manila Online Seller | November 11 Sale")

RESULTS_DIR = "results"

@st.cache_data
def load_results():
    revenue = pd.read_csv(
        os.path.join(RESULTS_DIR, "revenue_by_category.csv")
    )
    hourly = pd.read_csv(
        os.path.join(RESULTS_DIR, "orders_by_hour.csv")
    )
    regions = pd.read_csv(
        os.path.join(RESULTS_DIR, "region_summary.csv")
    )
    cancellations = pd.read_csv(
        os.path.join(RESULTS_DIR, "cancellation_by_payment.csv")
    )
    aov = pd.read_csv(
        os.path.join(RESULTS_DIR, "aov_summary.csv")
    )
    return revenue, hourly, regions, cancellations, aov

try:
    revenue, hourly, regions, cancellations, aov = load_results()

    total_revenue = float(aov["total_revenue"].iloc[0])
    total_orders = int(regions["order_count"].sum())
    total_cancelled = int(cancellations["cancelled_orders"].sum())
    total_payment_orders = int(cancellations["total_orders"].sum())
    cancellation_rate = (
        total_cancelled / total_payment_orders * 100
        if total_payment_orders else 0
    )
    average_order_value = float(
        aov["average_order_value"].iloc[0]
    )

    st.subheader("Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Delivered Revenue", f"₱{total_revenue:,.2f}")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Cancellation Rate", f"{cancellation_rate:.2f}%")
    c4.metric("Average Order Value", f"₱{average_order_value:,.2f}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Revenue by Category")
        st.bar_chart(
            revenue.set_index("category")["total_revenue"]
        )

    with right:
        st.subheader("Orders per Hour")
        st.line_chart(
            hourly.set_index("hour")["order_count"]
        )

    st.divider()
    st.subheader("Regional Performance")

    available_regions = sorted(
        regions["region"].dropna().unique().tolist()
    )
    selected_regions = st.multiselect(
        "Filter regions",
        options=available_regions,
        default=available_regions
    )

    filtered_regions = regions[
        regions["region"].isin(selected_regions)
    ]

    st.dataframe(filtered_regions, use_container_width=True)

    st.subheader("Cancellation Rate by Payment Method")
    st.dataframe(cancellations, use_container_width=True)
    
    st.divider()
    st.subheader("🤖 AI Sales Briefing")

    if st.button("Generate AI Briefing"):
        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"]
            )

            prompt = f"""
You are an analytics assistant for a Manila online seller's
November 11 sale.
Use only the summary numbers below. Do not invent facts or figures.
Write exactly 5 sentences and include one actionable
recommendation for next year's sale.

Delivered revenue: ₱{total_revenue:,.2f}
Total orders: {total_orders}
Cancellation rate: {cancellation_rate:.2f}%
Average order value: ₱{average_order_value:,.2f}

Revenue by category: {revenue.to_dict(orient="records")}
Orders by hour: {hourly.to_dict(orient="records")}
Regional summary: {filtered_regions.to_dict(orient="records")}
Cancellation by payment method: {cancellations.to_dict(orient="records")}
"""

            with st.spinner("Generating AI briefing..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

            st.write(response.text)

        except Exception:
            st.error(
                "AI briefing could not be generated. "
                "Please check your Gemini API key in Streamlit secrets."
            )

except Exception as e:
    st.error("Unable to load the results. Please check the CSV files in results/.")
    st.code(str(e))
