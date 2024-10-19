import pandas as pd
import json
df = pd.read_excel('table.xlsx')

questions = []

current_question = {
    'id':'',
    'text':'',
    'answers':[]
}

for row in df.to_records():
    if type(row[1]) == float:
        questions.append({
            'id':row[2],
            'text':row[3],
            'answers':[]
        })
    else:
        questions[-1]['answers'].append({
            'answer':row[4],
            'id':row[2],
            'parent_id':row[2],
            'next_id':row[5],
            'answer_type':row[6]
        })

file_name = 'questions.json'
json.dump(questions, open(file_name, mode='w', encoding='utf-8'),  ensure_ascii=False,)