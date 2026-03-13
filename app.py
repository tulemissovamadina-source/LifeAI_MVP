import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

        st.subheader("Карточка заметки")

        with st.container():
            st.markdown(f"### 📌 Тип: {data.get('Тип', '-')}")
            st.markdown(f"**⚡ Приоритет:** {data.get('Приоритет', '-')}")
            st.markdown(f"**📅 Дата:** {data.get('Дата', '-')}")
            st.markdown(f"**📝 Описание:** {data.get('Краткое описание', '-')}")
