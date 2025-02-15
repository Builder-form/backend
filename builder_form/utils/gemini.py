import google.generativeai as genai
import os
import json
from time import sleep
import pandas as pd
from pd_utils import append_df_to_excel
# gemini_api_key = os.environ["AIzaSyBlvoQLZsFJFQzhDYl964PNs-9yQXS6kVo"]

genai.configure(api_key='AIzaSyBlvoQLZsFJFQzhDYl964PNs-9yQXS6kVo')
model = genai.GenerativeModel('gemini-pro')

promt = """Представь что ты делаешь тест по строительству. У тебя есть вопросы, но некоторые термины могут быть непонятны пользователю\n
Найди среди текста полей text и всех полей answer строительные термины и дай им **строгие** определения на английском языке в виде\n
data:\n
[{
    "termin": "название термина",
    "description":"описание термина"
}, ...далее другие термины]\n
Ответь мне только json текстом, твой ответ должно быть возможно сделать содержимым json файла, определения на английском языке. Никакого текста больше писать не нужно.\n
Данные где искать строительные термины:\n"""



file = open('./questions.json')
data = json.load(file)


for row in data:
    response = model.generate_content(promt + json.dumps(row))
    df = pd.DataFrame()
    try:
        r = response.text
        r = r[r.find('['):r.find(']')+1]
        print(r)
        data = json.loads(r)
        df = pd.json_normalize(data)
        df['qid'] = [row['id'] for _ in range(len(df))]
        df.to_csv('termins.csv', mode='a', index = False, header=None)

    except: print('ERR')


    print(row['id'])
    sleep(10)


print(response.text)