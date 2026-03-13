import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = json.loads(st.secrets["gcp_service_account"]["json"])

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

gs_client = gspread.authorize(creds)
sheet = gs_client.open_by_key("12Ih5Mszzc1zF6ueu0YyanxL9EU_T4ereL5nIH-TR7Ac").sheet1

st.title("LifeAI Assistant")
st.write("Напиши мысль, задачу, встречу или идею")

user_input = st.text_area("Введите текст")

if st.button("Проанализировать"):
    if user_input.strip() == "":
        st.warning("Сначала введи текст")
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
Ты AI-ассистент. Анализируй заметку пользователя.

Определи:
- Тип: задача / идея / встреча / покупка / проект
- Приоритет: высокий / средний / низкий
- Дата: если указана, если нет — напиши "не указана"
- Краткое описание

Ответ дай строго в таком виде:

Тип: ...
Приоритет: ...
Дата: ...
Краткое описание: ...
"""
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        result = response.choices[0].message.content

        lines = result.split("\n")
        data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        st.session_state.current_note = {
            "Тип": data.get("Тип", "-"),
            "Приоритет": data.get("Приоритет", "-"),
            "Дата": data.get("Дата", "-"),
            "Описание": data.get("Краткое описание", "-")
        }

if "current_note" in st.session_state:
    note = st.session_state.current_note

    st.subheader("Карточка заметки")
    with st.container():
        st.markdown(f"### 📌 Тип: {note['Тип']}")
        st.markdown(f"**⚡ Приоритет:** {note['Приоритет']}")
        st.markdown(f"**📅 Дата:** {note['Дата']}")
        st.markdown(f"**📝 Описание:** {note['Описание']}")

    if st.button("Сохранить заметку"):
        sheet.append_row([
            note["Тип"],
            note["Приоритет"],
            note["Дата"],
            note["Описание"]
        ])
        st.success("Заметка сохранена в Google Sheets")


