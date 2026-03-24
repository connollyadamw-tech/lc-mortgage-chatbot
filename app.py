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

st.set_page_config(page_title="L&C Mortgage Insights Chatbot", page_icon="📊")
st.title("📊 L&C Mortgage Insights Chatbot")
st.caption("Ask questions about L&C mortgages, financial performance, conversions, and application volumes.")

uploaded_file = st.file_uploader("Upload a CSV file with L&C business data", type=["csv"])

data_context = ""

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("Preview of uploaded data")
    st.dataframe(df.head())

    data_context = df.to_csv(index=False)

st.subheader("Example questions")
st.write("- What were application volumes last month?")
st.write("- How have trading conversions changed over time?")
st.write("- Summarise historic financial performance trends.")
st.write("- What does the data suggest about recent mortgage demand?")

system_prompt = (
    "You are an internal business insights assistant for L&C Mortgages. "
    "You help users understand historic financial performance, trading conversions, "
    "application numbers, and business trends. "
    "Use the uploaded CSV data when available. "
    "Do not invent figures. "
    "If the answer is not in the provided data, say that clearly. "
    "Answer clearly, professionally, and briefly."
)

if uploaded_file is not None:
    system_prompt += f"\n\nHere is the available business data in CSV format:\n{data_context}"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

with st.sidebar:
    st.header("About")
    st.write("This chatbot is designed to answer questions about L&C mortgage business performance.")
    st.write("Upload a CSV to let the chatbot answer based on real data.")

    if st.button("Clear Chat"):
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.rerun()

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask about L&C mortgage performance, conversions, or applications...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )

            answer = response.choices[0].message.content
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
