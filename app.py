import streamlit as st
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

# -----------------------------
# Настройки страницы
# -----------------------------
st.set_page_config(page_title="LifeAI Assistant", layout="wide")

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
# Вспомогательные функции
# -----------------------------
def get_records_with_row_numbers(worksheet):
    """
    Читает таблицу и возвращает записи с номером строки.
    Это нужно, чтобы потом правильно обновлять статус "выполнена".
    """
    values = worksheet.get_all_values()

    if not values or len(values) < 2:
        return []

    headers = values[0]
    records = []

    for row_number, row in enumerate(values[1:], start=2):
        # если строка короче, чем количество заголовков — дополним пустыми значениями
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))

        record = dict(zip(headers, row))
        record["_row_number"] = row_number

        # подстраховка для старых записей
        if record.get("Статус", "").strip() == "":
            record["Статус"] = "активна"

        if record.get("Время", "").strip() == "":
            record["Время"] = "не указано"

        if record.get("Дата", "").strip() == "":
            record["Дата"] = "не указана"

        records.append(record)

    return records


def analyze_note(user_input: str):
    """
    Отправляет текст заметки в OpenAI и возвращает разобранные поля.
    """
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
- Время: если указано, если нет — напиши "не указано"
- Краткое описание

Ответ дай строго в таком виде:

Тип: ...
Приоритет: ...
Дата: ...
Время: ...
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

    return {
        "Тип": data.get("Тип", "-"),
        "Приоритет": data.get("Приоритет", "-"),
        "Дата": data.get("Дата", "не указана"),
        "Время": data.get("Время", "не указано"),
        "Описание": data.get("Краткое описание", "-")
    }


# -----------------------------
# Заголовок и навигация
# -----------------------------
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
    st.write("Это ваш AI-ассистент для управления задачами, идеями и встречами.")

    records = get_records_with_row_numbers(sheet)

    total_notes = len(records)
    active_notes = len([r for r in records if r.get("Статус", "активна") == "активна"])
    completed_notes = len([r for r in records if r.get("Статус", "") == "выполнена"])
    meetings = len([r for r in records if r.get("Тип", "").strip().lower() == "встреча"])
    tasks = len([r for r in records if r.get("Тип", "").strip().lower() == "задача"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего заметок", total_notes)
    col2.metric("Активные", active_notes)
    col3.metric("Выполненные", completed_notes)
    col4.metric("Встречи", meetings)

    st.write("")
    st.write("### Быстрая сводка")
    st.write(f"- Задачи: {tasks}")
    st.write(f"- Встречи: {meetings}")

    if records:
        st.write("### Последние заметки")
        latest_records = list(reversed(records))[:3]

        for record in latest_records:
            st.write(
                f"• {record.get('Тип', '-')} — {record.get('Описание', '-')} "
                f"({record.get('Статус', 'активна')})"
            )
    else:
        st.info("Пока нет сохранённых заметок")


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
            st.session_state.current_note = analyze_note(user_input)

    if "current_note" in st.session_state:
        note = st.session_state.current_note

        st.subheader("Карточка заметки")
        st.markdown(f"### 📌 Тип: {note.get('Тип', '-')}")
        st.markdown(f"**⚡ Приоритет:** {note.get('Приоритет', '-')}")
        st.markdown(f"**📅 Дата:** {note.get('Дата', 'не указана')}")
        st.markdown(f"**⏰ Время:** {note.get('Время', 'не указано')}")
        st.markdown(f"**📝 Описание:** {note.get('Описание', '-')}")

        if st.button("Сохранить заметку"):
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

            sheet.append_row([
                created_at,
                note.get("Тип", "-"),
                note.get("Приоритет", "-"),
                note.get("Дата", "не указана"),
                note.get("Время", "не указано"),
                note.get("Описание", "-"),
                "активна"
            ])

            st.success("Заметка сохранена в Google Sheets")
            st.session_state.voice_text = ""
            st.session_state.current_note = {}


# -----------------------------
# Все заметки
# -----------------------------
elif page == "Все заметки":
    st.subheader("Мои сохранённые заметки")

    records = get_records_with_row_numbers(sheet)

    filter_type = st.selectbox(
        "Выбери тип заметок",
        ["Все", "встреча", "задача", "идея", "покупка", "проект"]
    )

    filter_status = st.selectbox(
        "Статус",
        ["Все", "активна", "выполнена"]
    )

    sort_option = st.selectbox(
        "Сортировка",
        ["Без сортировки", "По приоритету", "Сначала новые"]
    )

    if records:
        filtered_records = records

        # фильтр по типу
        if filter_type != "Все":
            filtered_records = [
                record for record in filtered_records
                if record.get("Тип", "").strip().lower() == filter_type.lower()
            ]

        # фильтр по статусу
        if filter_status != "Все":
            filtered_records = [
                record for record in filtered_records
                if record.get("Статус", "активна").strip().lower() == filter_status.lower()
            ]

        # сортировка
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

        elif sort_option == "Сначала новые":
            filtered_records = list(reversed(filtered_records))

        if filtered_records:
            for i, record in enumerate(filtered_records, start=1):
                with st.expander(f"{i}. {record.get('Тип', '-')} — {record.get('Описание', '-')}"):

                    st.write(f"🕒 Создано: {record.get('Создано', '-')}")
                    st.write(f"📌 Тип: {record.get('Тип', '-')}")
                    st.write(f"⚡ Приоритет: {record.get('Приоритет', '-')}")
                    st.write(f"📅 Дата: {record.get('Дата', 'не указана')}")
                    st.write(f"⏰ Время: {record.get('Время', 'не указано')}")
                    st.write(f"📝 Описание: {record.get('Описание', '-')}")
                    st.write(f"📍 Статус: {record.get('Статус', 'активна')}")

                    if record.get("Статус", "активна") == "активна":
                        if st.button(f"✅ Выполнено {record['_row_number']}"):
                            sheet.update_cell(record["_row_number"], 7, "выполнена")
                            st.success("Задача отмечена выполненной")
                            st.rerun()
        else:
            st.info("По этим условиям заметок пока нет")
    else:
        st.info("Пока заметок нет")


# -----------------------------
# План на сегодня
# -----------------------------
elif page == "План на сегодня":
    st.subheader("📅 План на сегодня")

    if st.button("Показать план"):
        records = get_records_with_row_numbers(sheet)

        if records:
            active_records = [
                r for r in records
                if r.get("Статус", "активна") == "активна"
            ]

            priority_order = {
                "высокий": 1,
                "средний": 2,
                "низкий": 3
            }

            sorted_tasks = sorted(
                active_records,
                key=lambda r: priority_order.get(r.get("Приоритет", "").strip().lower(), 99)
            )

            if sorted_tasks:
                for i, task in enumerate(sorted_tasks[:5], start=1):
                    st.write(
                        f"{i}. {task.get('Тип', '-')} — {task.get('Описание', '-')}"
                        f" | {task.get('Дата', 'не указана')} | {task.get('Время', 'не указано')}"
                    )
            else:
                st.info("Активных задач пока нет")
        else:
            st.info("Задач пока нет")


# -----------------------------
# Итог дня
# -----------------------------
elif page == "Итог дня":
    st.subheader("🧠 Итог дня")

    if st.button("Сделать анализ дня"):
        records = get_records_with_row_numbers(sheet)

        if records:
            notes_text = "\n".join(
                [
                    f"{r.get('Тип', '-')} | {r.get('Приоритет', '-')} | {r.get('Статус', 'активна')} | {r.get('Описание', '-')}"
                    for r in records
                ]
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
3. сколько выполнено
4. что самое важное
5. что стоит сделать завтра

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
