import streamlit as st
from utils import refine_question, read_file_as_string

st.session_state.first_stage_response = "情況的總結"

example_prompt = read_file_as_string("example_prompt.txt")

st.write("最近有什麼煩惱?")
prompt = st.text_area('', key='prompt', value = example_prompt, height=200)
ask_button = st.button('確定')

if ask_button:
    with st.spinner("正在理解"):
        st.session_state.first_stage_response = refine_question(prompt)

st.write(st.session_state.first_stage_response)
