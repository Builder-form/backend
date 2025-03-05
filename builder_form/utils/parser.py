import pandas as pd
import json
import re

def parse_naming_conditions(text, question_id):
    conditions = []
    
    # Ищем условия вида "Q1_A1 - selected"
    condition_pattern = r'Q\d+_A\d+\s*-\s*selected'
    matches = re.finditer(condition_pattern, text)
    
    for match in matches:
        condition_text = match.group()
        answer_id = condition_text.split('-')[0].strip()
        question_id_part = answer_id.split('_')[0]  # Q1
        
        # Извлекаем соответствующий текстовый шаблон
        text_parts = text.split('\n')
        template = ''
        for i, part in enumerate(text_parts):
            if condition_text in part:
                # Берем следующую строку как шаблон
                if i + 1 < len(text_parts):
                    template = text_parts[i + 1].strip()
        
        if template:
            conditions.append({
                'parent_question_id': question_id,
                'left_operand_id': question_id_part,
                'condition_type': 'EQUAL',
                'right_operand_ids': [answer_id],
                'text_template': template
            })
    
    return conditions

df = pd.read_excel('table_v2.xlsx')

questions = []
naming_conditions = []

current_question = {
    'id': '',
    'text': '',
    'answers': []
}

for row in df.to_records():
    if type(row[1]) == float:
        questions.append({
            'id': row[2],
            'text': row[3],
            'answers': []
        })
        
        # Проверяем текст на наличие условий именования
        if isinstance(row[3], str):
            conditions = parse_naming_conditions(row[3], row[2])
            naming_conditions.extend(conditions)
            
    else:
        questions[-1]['answers'].append({
            'answer': row[4],
            'id': row[2],
            'parent_id': row[2],
            'next_id': row[5],
            'answer_type': row[6]
        })

# Сохраняем вопросы
# json.dump(questions, open('questions_from_table_v2.json', mode='w', encoding='utf-8'), ensure_ascii=False)

# Сохраняем условия именования
json.dump(naming_conditions, open('naming_conditions_v2.json', mode='w', encoding='utf-8'), ensure_ascii=False)