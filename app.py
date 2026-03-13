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

Тип:
Приоритет:
Дата:
Краткое описание:
"""
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        result = response.choices[0].message.content

        st.subheader("AI анализ")
        st.write(result)
