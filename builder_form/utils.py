import json
from .models import Question, Answer, AnswerTypes, Termin
import csv

def questionsJSONParse(jsonUrl):
    file = open(jsonUrl)
    data = json.load(file)
    for row in data:
        print(row['id'])
        question = Question.objects.create(
            id=row['id'],
            text_template=row['text']
        )
        for ans in row['answers']:
            print(ans['id'])
            try:
                Answer.objects.create(
                    text=ans['answer'],
                    id=ans['id'],
                    question=question,
                    next_id=ans['next_id'],
                    conditions= ans['conditions'],
                    type=ans['answer_type']
                )
            except:
                 Answer.objects.create(
                    text=ans['answer'],
                    id=ans['id'],
                    question=question,
                    next_id=ans['next_id'],
                    type=ans['answer_type']
                )
        

# questionsJSONParse('./utils/questions_test.json')

def terminCSVParse(csvUrl):
    file = open(csvUrl)
    reader = csv.reader(file)
    for line in reader:
        print(line[2], line[0])
        Termin.objects.create(
            termin=line[0],
            description=line[1],
            qid=line[2]
        )

# terminCSVParse('/utils/termin.csv')
    
