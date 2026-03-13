from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        import streamlit as st

st.title("LifeAI MVP")
st.write("Простейший прототип AI-ассистента")

text_note = st.text_area("Напишите заметку:")

if st.button("Сохранить текст"):
    st.write("Вы написали:", text_note)

audio_file = st.file_uploader("Загрузите аудио (mp3/wav):", type=["mp3", "wav"])
if audio_file is not None:

    st.write("Аудио загружено:", audio_file.name)
