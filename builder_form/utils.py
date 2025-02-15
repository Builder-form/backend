import json
from .models import Question, Answer, AnswerTypes, Termin, NamingCondition
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
        

# u.questionsJSONParse('./builder_form/utils/questions.json')

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

#u.terminCSVParse('./builder_form/utils/termins.csv')
    

def namingConditionsJSONParse(jsonUrl):
    file = open(jsonUrl)
    data = json.load(file)
    for row in data:
        parent_question = Question.objects.get(id=row['parent_question_id'])
        print(row['parent_question_id'], row['left_operand_id'])
        condition = NamingCondition.objects.create(
            parent_question=parent_question,
            left_operand=Question.objects.get(id=row['left_operand_id']),
            condition_type=row['condition_type'],
            text_template=row['text_template']
        )
        condition.right_operand.set(Answer.objects.filter(id__in=row['right_operand_ids']))

#namingConditionsJSONParse('./utils/naming_conditions.json')