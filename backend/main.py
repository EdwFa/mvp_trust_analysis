from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
from openai import OpenAI
import os
import base64
import json
import xmltodict
from validator import CrossValidator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Trust Analysis API")

# Разрешаем CORS для Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
def analyze_documents(
    xml_file: UploadFile = File(...),
    pdf_file: UploadFile = File(...),
    ollama_url: str = Form(...),
    ollama_model: str = Form(...)
):
    # --- Agent 1: Parsing XML ---
    try:
        xml_content = xml_file.file.read().decode('utf-8')
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга XML: {str(e)}")

    # --- Agent 2: Parsing PDF via Ollama ---
    try:
        pdf_bytes = pdf_file.file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        base64_images = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("jpeg")
            b64_str = base64.b64encode(img_data).decode("utf-8")
            base64_images.append(b64_str)
            
        if not base64_images:
            raise HTTPException(status_code=400, detail="Не удалось извлечь страницы из PDF")
            
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
        if llm_result.startswith("```json"):
            llm_result = llm_result.replace("```json", "").replace("```", "").strip()
        elif llm_result.startswith("```"):
            llm_result = llm_result.replace("```", "").strip()
            
        pdf_json = json.loads(llm_result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Ollama вернула невалидный JSON: {llm_result}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Ollama: {str(e)}")

    # --- Agent 3: Cross Validation ---
    try:
        validator = CrossValidator()
        validation_result = validator.validate(xml_json, pdf_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка валидации: {str(e)}")

    # Return full state to frontend
    return {
        "agent1_xml": xml_json,
        "agent2_pdf": pdf_json,
        "agent3_validation": validation_result,
        "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')  # Передаем обратно для модалки в UI, если надо, или фронт сам отобразит
    }
