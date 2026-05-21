import streamlit as st
import pandas as pd
import json
import fitz  # PyMuPDF
from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
import xmltodict
from validator import CrossValidator

st.set_page_config(page_title='Анализ Доверенности', layout='wide')

@st.dialog("Оригинал доверенности", width="large")
def show_pdf_modal(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0" width="100%" height="800px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

st.title('MVP: Анализ Заявления и Доверенности')
st.markdown("Загрузите заявление (XML) и доверенность (PDF). Система проанализирует их и выдаст структурированный результат (JSON), после чего сверит данные.")

# Sidebar for API Key / URL
with st.sidebar:
    st.header("Настройки Ollama")
    
    # URL для локального Ollama
    env_ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    ollama_url = st.text_input("Ollama API URL", value=env_ollama_url)
    
    # Имя модели Ollama
    ollama_model = st.text_input("Название модели", value="qwen3-vl:30b")
    
    st.caption("Приложение настроено на работу с локальным Ollama. Ключ API не требуется.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Заявление (XML)")
    xml_file = st.file_uploader('Загрузить XML', type=['xml'])
    
with col2:
    st.header("2. Доверенность (PDF)")
    pdf_file = st.file_uploader('Загрузить PDF', type=['pdf'])
    if pdf_file:
        if st.button("👁️ Посмотреть оригинал PDF"):
            show_pdf_modal(pdf_file.getvalue())

if st.button("Проанализировать", type="primary"):
    if not xml_file or not pdf_file:
        st.warning("Пожалуйста, загрузите оба файла: XML и PDF.")
    elif not ollama_url:
        st.warning("Пожалуйста, укажите URL для Ollama в боковом меню.")
    else:
        st.markdown("---")
        res_col1, res_col2 = st.columns(2)
        
        xml_json = None
        pdf_json = None
        
        # Agent 1: XML to JSON
        with res_col1:
            with st.spinner("Агент 1: Чтение и систематизация XML..."):
                try:
                    xml_content = xml_file.read().decode('utf-8')
                    parsed_xml = xmltodict.parse(xml_content)
                    
                    xml_json = []
                    for root_key, root_val in parsed_xml.items():
                        if isinstance(root_val, dict):
                            for sub_key, sub_val in root_val.items():
                                if isinstance(sub_val, list):
                                    xml_json.extend(sub_val)
                                elif isinstance(sub_val, dict):
                                    xml_json.append(sub_val)
                        elif isinstance(root_val, list):
                            xml_json.extend(root_val)
                    
                    if not xml_json:
                        xml_json = [parsed_xml]
                        
                    st.success("Агент 1 успешно обработал заявление (XML).")
                    with st.expander(f"Посмотреть JSON Заявления (Агент 1) — найдено {len(xml_json)} записей", expanded=False):
                        st.json(xml_json)
                except Exception as e:
                    st.error(f"Ошибка при обработке XML: {e}")
                    
        # Agent 2: PDF to JSON via LLM
        with res_col2:
            with st.spinner("Агент 2: Конвертация PDF в изображения и распознавание..."):
                if xml_json is not None:
                    try:
                        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
                        base64_images = []
                        for i in range(len(doc)):
                            page = doc.load_page(i)
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            img_data = pix.tobytes("jpeg")
                            b64_str = base64.b64encode(img_data).decode("utf-8")
                            base64_images.append(b64_str)
                        
                        if not base64_images:
                            st.error("Не удалось извлечь страницы из PDF.")
                        else:
                            st.info(f"PDF конвертирован ({len(base64_images)} стр). Отправляем в Ollama...")
                            client = OpenAI(base_url=ollama_url, api_key="ollama")
                            system_prompt = '''Ты - AI-агент, анализирующий сканы доверенностей.
Твоя задача: извлечь ключевую информацию из предоставленных изображений доверенности и вернуть её СТРОГО в формате JSON.
Ожидаемые поля (на английском ключи, на русском или в виде цифр значения):
- "trustor": Доверитель (ФИО или название компании)
- "trustor_inn": ИНН Доверителя (строка цифр, если есть)
- "trustor_ogrn": ОГРН Доверителя (строка цифр, если есть)
- "trustee": Доверенное лицо (ФИО)
- "issue_date": Дата выдачи
- "expiry_date": Срок действия
- "powers": Список полномочий (массив строк)
- "notary": Нотариус (если указан)

Верни ТОЛЬКО валидный JSON без маркдауна и прочих символов.'''

                            user_content = [{"type": "text", "text": "Пожалуйста, проанализируй эти страницы доверенности и извлеки нужную информацию."}]
                            for b64 in base64_images:
                                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                            response = client.chat.completions.create(
                                model=ollama_model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_content}
                                ],
                                temperature=0.0
                            )
                            
                            llm_result = response.choices[0].message.content
                            try:
                                if llm_result.startswith("```json"):
                                    llm_result = llm_result.replace("```json", "").replace("```", "").strip()
                                elif llm_result.startswith("```"):
                                    llm_result = llm_result.replace("```", "").strip()
                                    
                                pdf_json = json.loads(llm_result)
                                st.success("Агент 2 успешно проанализировал доверенность.")
                                with st.expander("Посмотреть JSON Доверенности (Агент 2)", expanded=False):
                                    st.json(pdf_json)
                            except json.JSONDecodeError:
                                st.warning("Ответ LLM не является чистым JSON. Вывод текста:")
                                st.code(llm_result)
                    except Exception as e:
                        st.error(f"Ошибка при обработке PDF или обращении к LLM: {e}")
        
        # Agent 3: Сверка данных (На всю ширину экрана под колонками)
        if xml_json is not None and pdf_json is not None:
            st.markdown("---")
            with st.spinner("Агент 3: Сверка данных (XML vs PDF)..."):
                validator = CrossValidator()
                validation_result = validator.validate(xml_json, pdf_json)
                
                if validation_result["status"] == "Matched":
                    st.success(f"Агент 3: Найдено совпадение! (Совпало полей: {validation_result['matched_fields']} из {validation_result['total_fields']})")
                else:
                    st.error(f"Агент 3: Полного совпадения не найдено. (Лучший результат: {validation_result['matched_fields']} из {validation_result['total_fields']})")
                
                with st.expander("Детали сверки (Агент 3)", expanded=True):
                    for det in validation_result["details"]:
                        icon = "✅" if det["matched"] else "❌"
                        st.markdown(f"**{det['field']}**: `{det['pdf_value']}` {icon}")
                    
                    st.subheader("Самая подходящая запись из XML:")
                    st.json(validation_result["best_xml_row"])
