import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

# -----------------------------
# Подключение OpenAI
# -----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Подключение Google Sheets
# -----------------------------
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

# -----------------------------
# Настройки страницы
# -----------------------------
st.set_page_config(page_title="LifeAI Assistant", layout="wide")

st.title("LifeAI Assistant")

page = st.sidebar.radio(
    "Навигация",
    [
        "Главная",
        "Новая заметка",
        "Все заметки",
        "План на сегодня",
        "Итог дня"
    ]
)

# -----------------------------
# Главная
# -----------------------------
if page == "Главная":
    st.subheader("Добро пожаловать")
    st.write("Это ваш AI-ассистент для управления мыслями, задачами, встречами и идеями.")
    st.write("Что уже умеет приложение:")
    st.write("- анализировать заметки через AI")
    st.write("- сохранять заметки в Google Sheets")
    st.write("- показывать все заметки")
    st.write("- фильтровать и сортировать их")
    st.write("- формировать план на сегодня")
    st.write("- делать итог дня")

# -----------------------------
# Новая заметка
# -----------------------------
elif page == "Новая заметка":
    st.subheader("🎤 Голосовая заметка")

    audio_file = st.file_uploader(
        "Загрузи аудиофайл (mp3, wav, m4a)",
        type=["mp3", "wav", "m4a"]
    )

    if audio_file is not None:
        st.audio(audio_file)

        if st.button("Распознать голос"):
            with st.spinner("Распознаю голос..."):
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                st.session_state.voice_text = transcript.text
                st.success("Голос распознан")

    st.subheader("✍ Текстовая заметка")

    default_text = st.session_state.get("voice_text", "")
    user_input = st.text_area("Введите текст", value=default_text)

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
        st.markdown(f"### 📌 Тип: {note['Тип']}")
        st.markdown(f"**⚡ Приоритет:** {note['Приоритет']}")
        st.markdown(f"**📅 Дата:** {note['Дата']}")
        st.markdown(f"**📝 Описание:** {note['Описание']}")

    if st.button("Сохранить заметку"):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        sheet.append_row([
            created_at,
            note["Тип"],
            note["Приоритет"],
            note["Дата"],
            note["Время"],
            note["Описание"],
            "активна"
])

    st.success("Заметка сохранена в Google Sheets")

# -----------------------------
# Все заметки
# -----------------------------
elif page == "Все заметки":
    st.subheader("Мои сохранённые заметки")

    records = sheet.get_all_records()

    filter_type = st.selectbox(
        "Выбери тип заметок",
        ["Все", "встреча", "задача", "идея", "покупка", "проект"]
    )

    sort_option = st.selectbox(
        "Сортировка",
        ["Без сортировки", "По приоритету"]
    )

    if records:
        filtered_records = records

        if filter_type != "Все":
            filtered_records = [
                record for record in records
                if record.get("Тип", "").strip().lower() == filter_type.lower()
            ]

        if sort_option == "По приоритету":
            priority_order = {
                "высокий": 1,
                "средний": 2,
                "низкий": 3
            }

            filtered_records = sorted(
                filtered_records,
                key=lambda record: priority_order.get(
                    record.get("Приоритет", "").strip().lower(),
                    99
                )
            )

        if filtered_records:
            for i, record in enumerate(filtered_records, start=1):
                with st.expander(f"{i}. {record.get('Тип', '-')} — {record.get('Описание', '-')}"):

                    st.write(f"🕒 Создано: {record.get('Создано', '-')}")
                    st.write(f"📌 Тип: {record.get('Тип', '-')}")
                    st.write(f"⚡ Приоритет: {record.get('Приоритет', '-')}")
                    st.write(f"📅 Дата: {record.get('Дата', '-')}")
                    st.write(f"⏰ Время: {record.get('Время', '-')}")
                    st.write(f"📝 Описание: {record.get('Описание', '-')}")

                    status = record.get("Статус", "").strip()
                    if status == "":
                        status = "активна"

                    st.write(f"📍 Статус: {status}")

                    if status == "активна":
                        if st.button(f"✅ Выполнено {i}"):
                            row_number = i + 1
                            sheet.update_cell(row_number, 7, "выполнена")
                            st.success("Задача отмечена выполненной")
                            st.rerun()
        else:
            st.info("По этому типу заметок пока нет")
    else:
        st.info("Пока заметок нет")
# -----------------------------
# План на сегодня
# -----------------------------
elif page == "План на сегодня":
    st.subheader("📅 План на сегодня")

    if st.button("Показать план"):
        records = sheet.get_all_records()

        if records:
            priority_order = {
                "высокий": 1,
                "средний": 2,
                "низкий": 3
            }

            sorted_tasks = sorted(
                records,
                key=lambda r: priority_order.get(r["Приоритет"].strip().lower(), 99)
            )

            for i, task in enumerate(sorted_tasks[:5], start=1):
                st.write(f"{i}. {task['Тип']} — {task['Описание']}")
        else:
            st.info("Задач пока нет")

# -----------------------------
# Итог дня
# -----------------------------
elif page == "Итог дня":
    st.subheader("🧠 Итог дня")

    if st.button("Сделать анализ дня"):
        records = sheet.get_all_records()

        if records:
            notes_text = "\n".join(
                [f"{r['Тип']} | {r['Приоритет']} | {r['Описание']}" for r in records]
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """
Ты AI ассистент. Проанализируй список заметок пользователя.

Сделай краткий итог:
1. сколько задач
2. сколько встреч
3. что самое важное
4. что стоит сделать завтра

Ответ сделай кратким и понятным.
"""
                    },
                    {
                        "role": "user",
                        "content": notes_text
                    }
                ]
            )

            summary = response.choices[0].message.content
            st.write(summary)
        else:
            st.info("Сегодня пока нет заметок")
