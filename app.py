import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------
# Load API Key
# ---------------------------
load_dotenv()

api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Missing OPENAI_API_KEY. Add it in Streamlit Secrets or your local .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------------------------
# Page Setup
# ---------------------------
st.set_page_config(page_title="L&C Mortgage Insights", page_icon="lc_logo.png", layout="wide")

st.image("lc_logo.png", width=180)
st.title("L&C AI Insights")
st.caption("AI-powered insights to make the best business decisions")

# ---------------------------
# Load Data
# ---------------------------
data_file = "sample_lc_mortgage_data.csv"
raw_df = None

if os.path.exists(data_file):
    raw_df = pd.read_csv(data_file)

uploaded_file = st.file_uploader("Upload your own CSV", type=["csv"])

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)

# ---------------------------
# Process Data
# ---------------------------
chart_df = None
data_summary = ""
ratio_df = None

if raw_df is not None:
    raw_df = raw_df.rename(columns={"Unnamed: 0": "category"})
    raw_df["category"] = raw_df["category"].astype(str).str.strip()

    month_columns = [col for col in raw_df.columns if col != "category"]

    df_long = raw_df.melt(
        id_vars="category",
        value_vars=month_columns,
        var_name="month",
        value_name="value"
    )

    df_long["month_date"] = pd.to_datetime(df_long["month"], format="%b-%y", errors="coerce")
    df_long = df_long.sort_values(["month_date", "category"])

    chart_df = df_long.pivot(index="month_date", columns="category", values="value").fillna(0)
    chart_df = chart_df.sort_index()

    # Derived metrics
    ratio_df = chart_df.copy()

    if "Mortgages" in ratio_df.columns and "Protection" in ratio_df.columns:
        ratio_df["Protection_to_Mortgages_%"] = (
            ratio_df["Protection"] / ratio_df["Mortgages"] * 100
        ).round(2)

    if "Mortgages" in ratio_df.columns and "Conveyancing" in ratio_df.columns:
        ratio_df["Conveyancing_to_Mortgages_%"] = (
            ratio_df["Conveyancing"] / ratio_df["Mortgages"] * 100
        ).round(2)

    # KPI section
    st.subheader("Data Overview")
    col1, col2, col3 = st.columns(3)

    if "Mortgages" in chart_df.columns:
        col1.metric("Total Mortgages", f"{int(chart_df['Mortgages'].sum()):,}")
    else:
        col1.metric("Total Mortgages", "N/A")

    if "Protection" in chart_df.columns:
        col2.metric("Total Protection", f"{int(chart_df['Protection'].sum()):,}")
    else:
        col2.metric("Total Protection", "N/A")

    if "Conveyancing" in chart_df.columns:
        col3.metric("Total Conveyancing", f"{int(chart_df['Conveyancing'].sum()):,}")
    else:
        col3.metric("Total Conveyancing", "N/A")

    # Extra KPI ratios
    st.subheader("Key Ratios")
    r1, r2 = st.columns(2)

    if "Protection_to_Mortgages_%" in ratio_df.columns:
        r1.metric(
            "Average Protection to Mortgages %",
            f"{ratio_df['Protection_to_Mortgages_%'].mean():.2f}%"
        )
    else:
        r1.metric("Average Protection to Mortgages %", "N/A")

    if "Conveyancing_to_Mortgages_%" in ratio_df.columns:
        r2.metric(
            "Average Conveyancing to Mortgages %",
            f"{ratio_df['Conveyancing_to_Mortgages_%'].mean():.2f}%"
        )
    else:
        r2.metric("Average Conveyancing to Mortgages %", "N/A")

    # Charts
    st.subheader("Trend Chart")
    categories = list(chart_df.columns)

    chart_choice = st.selectbox(
        "Select series to view",
        options=["All"] + categories
    )

    if chart_choice == "All":
        st.line_chart(chart_df)
    else:
        st.line_chart(chart_df[[chart_choice]])

    if ratio_df is not None:
        ratio_options = [c for c in ratio_df.columns if c.endswith("%")]
        if ratio_options:
            st.subheader("Conversion Ratio Chart")
            ratio_choice = st.selectbox("Select ratio to view", ratio_options)
            st.line_chart(ratio_df[[ratio_choice]])

    # Previews
    st.subheader("Raw Data Preview")
    st.dataframe(raw_df, hide_index=True, use_container_width=True)

    st.subheader("Calculated Data Preview")
    preview_df = ratio_df.reset_index().copy()
    preview_df["month_date"] = preview_df["month_date"].dt.strftime("%b-%Y")
    st.dataframe(preview_df, hide_index=True, use_container_width=True)

    # Build prompt summary
    summary_lines = []

    for category in chart_df.columns:
        series = chart_df[category]
        peak_month = series.idxmax()
        low_month = series.idxmin()

        summary_lines.append(
            f"{category}: total={int(series.sum())}, "
            f"average={round(series.mean(), 1)}, "
            f"highest={int(series.max())} in {peak_month.strftime('%b-%Y')}, "
            f"lowest={int(series.min())} in {low_month.strftime('%b-%Y')}"
        )

    if "Protection_to_Mortgages_%" in ratio_df.columns:
        series = ratio_df["Protection_to_Mortgages_%"]
        summary_lines.append(
            f"Protection to Mortgages ratio: average={series.mean():.2f}%, "
            f"highest={series.max():.2f}% in {series.idxmax().strftime('%b-%Y')}, "
            f"lowest={series.min():.2f}% in {series.idxmin().strftime('%b-%Y')}"
        )

    if "Conveyancing_to_Mortgages_%" in ratio_df.columns:
        series = ratio_df["Conveyancing_to_Mortgages_%"]
        summary_lines.append(
            f"Conveyancing to Mortgages ratio: average={series.mean():.2f}%, "
            f"highest={series.max():.2f}% in {series.idxmax().strftime('%b-%Y')}, "
            f"lowest={series.min():.2f}% in {series.idxmin().strftime('%b-%Y')}"
        )

    compact_table = ratio_df.reset_index().copy()
    compact_table["month_date"] = compact_table["month_date"].dt.strftime("%b-%Y")

    data_summary = "Summary statistics:\n" + "\n".join(summary_lines)
    data_summary += "\n\nMonthly data:\n" + compact_table.to_csv(index=False)

# ---------------------------
# System Prompt
# ---------------------------
system_prompt = f"""
You are a senior business analyst for L&C Mortgages.

Answer in this format:

Conclusion:
(1 sentence summary)

Key Insights:
- Bullet point with numbers
- Bullet point with trend
- Bullet point with comparison

Rules:
- Only use the data provided
- Do not invent figures
- If something is not present in the data, say so clearly
- Answer in a concise, professional, analyst-style tone
- Highlight trends, peaks, troughs, and notable changes over time
- When helpful, compare categories across months
- If asked about conversion of Protection to Mortgages, use the Protection_to_Mortgages_% field
- If asked about conversion of Conveyancing to Mortgages, use the Conveyancing_to_Mortgages_% field

Here is the dataset:
{data_summary}
"""

# ---------------------------
# Chat Memory
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

with st.sidebar:
    st.header("About")
    st.write("This chatbot is designed to answer questions about L&C mortgage business performance.")
    st.write("Upload a CSV to let the chatbot answer based on real data.")

    if st.button("Clear Chat"):
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.rerun()

# ---------------------------
# Example Questions
# ---------------------------
st.subheader("Example questions")
st.write("- Summarise the main mortgage trend over the full period.")
st.write("- Which month had the highest mortgage volume?")
st.write("- What is the average protection to mortgages conversion?")
st.write("- Which month had the best protection to mortgages conversion?")
st.write("- What are the key trends in conveyancing?")

# ---------------------------
# Display Chat
# ---------------------------
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------
# Chat Input
# ---------------------------
user_input = st.chat_input("Ask about L&C mortgage performance, conversions, or applications...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analysing data..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    temperature=0.2
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"OpenAI API error: {str(e)}")
