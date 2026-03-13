import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("LifeAI Assistant")
st.write("Напиши мысль, задачу, встречу или идею")

if "saved_notes" not in st.session_state:
    st.session_state.saved_notes = []

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
        st.session_state.saved_notes.append(note.copy())
        st.success("Заметка сохранена")

if st.session_state.saved_notes:
    st.subheader("Сохранённые заметки")

    for i, note in enumerate(st.session_state.saved_notes, start=1):
        with st.expander(f"{i}. {note['Тип']} — {note['Описание']}"):
            st.write(f"📌 Тип: {note['Тип']}")
            st.write(f"⚡ Приоритет: {note['Приоритет']}")
            st.write(f"📅 Дата: {note['Дата']}")
            st.write(f"📝 Описание: {note['Описание']}")
