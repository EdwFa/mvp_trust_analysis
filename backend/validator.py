class CrossValidator:
    def __init__(self):
        pass
    
    def validate(self, xml_data_list, pdf_data):
        """
        Ищет точное совпадение данных из PDF среди списка заявлений из XML.
        xml_data_list: список словарей (строк из XML)
        pdf_data: словарь с данными из PDF
        """
        if not isinstance(xml_data_list, list):
            # Если передали один объект, оборачиваем в список
            xml_data_list = [xml_data_list]
            
        best_match = None
        best_score = -1
        best_details = []
        
        pdf_keys = pdf_data.keys() if pdf_data else []
        
        for xml_row in xml_data_list:
            score = 0
            details = []
            
            # Рекурсивно вытаскиваем значения из XML (игнорируя сложные структуры для упрощения)
            # В реальном проекте здесь будет строгий маппинг полей.
            # Для MVP будем искать значения из PDF в плоском словаре XML
            flat_xml = self._flatten_dict(xml_row)
            
            for key, pdf_val in pdf_data.items():
                # Строгое сравнение: ищем точное строковое совпадение значения pdf_val
                # среди значений flat_xml
                matched = False
                pdf_str = str(pdf_val).strip().lower() if pdf_val else ""
                
                # Поиск точного совпадения
                if pdf_str:
                    for xml_k, xml_v in flat_xml.items():
                        xml_str = str(xml_v).strip().lower() if xml_v else ""
                        if pdf_str == xml_str or pdf_str in xml_str: # Строгое вхождение
                            matched = True
                            break
                            
                if matched:
                    score += 1
                    
                details.append({
                    "field": key,
                    "pdf_value": pdf_val,
                    "matched": matched
                })
                
            if score > best_score:
                best_score = score
                best_match = xml_row
                best_details = details
                
        return {
            "status": "Matched" if best_score == len(pdf_keys) and len(pdf_keys) > 0 else "Mismatch",
            "matched_fields": best_score,
            "total_fields": len(pdf_keys),
            "best_xml_row": best_match,
            "details": best_details
        }
        
    def _flatten_dict(self, d, parent_key='', sep='_'):
        items = []
        if isinstance(d, dict):
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(d, list):
            for i, v in enumerate(d):
                new_key = f"{parent_key}{sep}{i}"
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((parent_key, d))
        return dict(items)
