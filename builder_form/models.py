from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import json
from django.utils import timezone
from user.models import User
from django.core.exceptions import ValidationError
import re
class AnswerTypes(models.TextChoices):
    SINGLE = 'SINGLE', _("Single")
    NQONE = 'MULTI - NQ ONE', _('MULTI - NQ ONE')
    CUSTOM = 'CUSTOM', _('Custom')
    NQEACH = 'MULTI - NQ EACH', _('MULTI - NQ EACH')
    NUMBEREACH = 'NUMBER EACH', _('NUMBER EACH')

class ConditionTypes(models.TextChoices):
    EQUAL = 'EQUAL', _('Equal')
    NOT_EQUAL = 'NOT_EQUAL', _('Not Equal')
    # GREATER_THAN = 'GREATER_THAN', _('Greater Than')
    # LESS_THAN = 'LESS_THAN', _('Less Than')
    # IN = 'IN', _('In')
    # NOT_IN = 'NOT_IN', _('Not In')
    # CONTAINS = 'CONTAINS', _('Contains')
    # NOT_CONTAINS = 'NOT_CONTAINS', _('Not Contains')
    # ANSWERED = 'ANSWERED', _('Answered')
    # NOT_ANSWERED = 'NOT_ANSWERED', _('Not Answered')
    

class Question(models.Model):
    id = models.CharField(_("id"), max_length=50, primary_key=True)
    text_template = models.CharField(_("text_template"), max_length=1000)



class Answer(models.Model):
    text = models.CharField(_("text"), max_length=300)
    id = models.CharField(_("id"), max_length=50, primary_key=True)
    question =  models.ForeignKey(Question, verbose_name=_("question_id"), on_delete=models.CASCADE)
    next_id = models.CharField(_("next id"), max_length=50)#id to which the code will go in any case if no condition is met or if there are no conditions at all
    conditions = models.TextField(_("conditions"), max_length=10000, default='{"params": "", "conditions":"", "insertion": "Left"}') #{params: string, conditions:string, insertion: 'Left'|'Right'|'After equvalent questions'}
    type = models.CharField(max_length=300, choices=AnswerTypes.choices, default=AnswerTypes.SINGLE)


class Termin(models.Model):
    termin = models.CharField(_("Termin"), max_length=300)
    description = models.CharField(_("Description"), max_length=1000)
    qid = models.CharField(_("ID"), max_length=50)


class Project(models.Model):
    name = models.CharField(_("Name"), max_length=300)
    id = models.UUIDField( default=uuid.uuid4, editable=False, primary_key=True, )
    questions_queue = models.CharField(_("Questions queue"), max_length=10000, default='', blank=True)
    last_edit = models.DateTimeField(_("last_edit"), blank=True)
    created = models.DateTimeField(_("created"), editable=False)
    history_queue = models.CharField(_("History queue"), max_length=10000, default='', blank=True)
    user = models.ForeignKey(User, verbose_name=_("User"), to_field='username', on_delete=models.CASCADE)



    def back(self):
        current_question = self.get_current_question()
        current_question.delete()

        history = list(self.history_queue.split(','))
        last_answered_question_instance = QuestionInstance.objects.get(pk=history[-1])
        last_answered_question = Question.objects.get(id=last_answered_question_instance.qid)

        last_answers = AnswerQuestion.objects.all().filter(answer__question=last_answered_question)

        for ans in last_answers:
            ans.delete()
        
        history.pop()

        self.history_queue = ','.join(history)
        self.questions_queue =  str(last_answered_question_instance.pk) + ',' + self.questions_queue

        self.save()

        return last_answered_question_instance  

    def formatAnswers(self, answers):
        a = ''
        for ans in answers:
            a+=f"<div>&emsp;* {ans}\n</div>"
        return a
        
    def formatPairAnswers(self, answers1, answers2):
        a = ''
       
        m = max(len(answers1), len(answers2))
        mi = min(len(answers1), len(answers2))
        if mi == 0: return a
        for i in range(m):
            if mi == len(answers2):
                a += f'<div>&emsp;* {answers1[i]} - {answers2[i%(mi)]}</div>'
            else:
                a += f'<div>&emsp;* {answers1[i%mi]} - {answers2[i]}</div>'

        return a
    
    def generate_room_report(self, parent_pk):
        report = ""
        answers = AnswerQuestion.objects.filter(project=self)

        def get_answer(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            for a in ans:
                try:
                    q = QuestionInstance.objects.get(pk=a.question_instance)
                except:
                    return ""
                
                while q.parent_pk != parent_pk:
                    try:
                        q = QuestionInstance.objects.get(pk=q.parent_pk)
                    except:
                        break
                
                if q.parent_pk == parent_pk:
                    return a.answer_text
            
            return ""

        def get_answers(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            
            answers_text = []
            
            for a in ans:
                try:
                    q = QuestionInstance.objects.get(pk=a.question_instance)
                except:
                    return answers_text
                while q.parent_pk != parent_pk:
                    try:
                        q = QuestionInstance.objects.get(pk=q.parent_pk)
                    except:
                        break
                
                if q.parent_pk == parent_pk:
                    answers_text.append(a.answer_text)
            
            return answers_text
        
       
    
        def addStringReport(string, qid):
            nonlocal report
            if get_answer(qid) == '' and int(qid[1:]) > 46:
                return
            else:
                report += string
        
        
        
        report += f"<strong>Room purposes</strong>: {', '.join(get_answers('Q30'))}  {', '.join(get_answers('Q31'))}  {', '.join(get_answers('Q32'))} \n\n"
        
        report += "<strong>RN.1) Strip out and demolition</strong>:\n\n"
        report += "<strong>Room type specific:\n</strong>"

        for q in range(34, 46, 2):
            addStringReport(self.formatPairAnswers(get_answers(f'Q{q}'), get_answers(f'Q{q+1}')) , f'Q{q}')
        
        addStringReport("Ceilings:\n", 'Q46')
        addStringReport(self.formatAnswers(get_answers('Q46')), 'Q46')

        addStringReport("Walls:\n", 'Q47')
        addStringReport(self.formatPairAnswers(get_answers('Q47'),get_answers('Q48')), 'Q47')

        addStringReport("Floors:\n", 'Q49')
        addStringReport(self.formatPairAnswers(get_answers('Q49'),get_answers('Q50')), 'Q49')

        addStringReport("\nRN.2) Structure improvement:\n", 'Q52')
        addStringReport("Ceilings:\n", 'Q52')
        addStringReport(self.formatAnswers(get_answers('Q52')), 'Q52')

        addStringReport("Walls:\n", 'Q53')
        addStringReport(self.formatAnswers(get_answers('Q53')), 'Q53')

        addStringReport("Floors:\n", 'Q54')
        addStringReport(self.formatAnswers(get_answers('Q54')), 'Q54')
        
        addStringReport("\nRN.3) Internal decoration and finishes:\n", 'Q56')
        addStringReport("Ceilings:\n", 'Q56')
        addStringReport(self.formatAnswers(get_answers('Q56')), 'Q56')

        addStringReport("Walls:\n", 'Q57')
        addStringReport(self.formatPairAnswers(get_answers('Q57'),get_answers('Q58')), 'Q57')

        addStringReport("Floors:\n", 'Q59')
        addStringReport(self.formatPairAnswers(get_answers('Q59'),get_answers('Q60')), 'Q59')
        
        addStringReport("Woodwork:\n", 'Q61')
        addStringReport(self.formatAnswers(get_answers('Q61')), 'Q61')

        addStringReport("\nRN.4) Fitting and installing:\n", 'Q63')
        addStringReport("Windows:\n", 'Q63')
        addStringReport(self.formatPairAnswers(get_answers('Q63'),get_answers('Q64')), 'Q63')

        addStringReport("External doors:\n", 'Q641')
        addStringReport(self.formatPairAnswers(get_answers('Q641'),get_answers('Q642')), 'Q641')

        addStringReport("Internal doors:\n", 'Q65')
        addStringReport(self.formatPairAnswers(get_answers('Q65'),get_answers('Q66')), 'Q65')

        addStringReport("Inside rooms/hallway/landings:\n", 'Q67')
        addStringReport(self.formatPairAnswers(get_answers('Q67'),get_answers('Q68')), 'Q67')

        addStringReport("Electrics:\n", 'Q69')
        addStringReport(self.formatPairAnswers(get_answers('Q69'),get_answers('Q691')), 'Q69')


        if get_answers('Q31') in ['Q31_A1', 'Q31_A2']:
            report += "Room type specific:\n"
            report += "Kitchen / Ulitity:\n"
            for q in range(70, 87, 2):
                addStringReport(self.formatPairAnswers(get_answers('Q{q}'),get_answers(f'Q{q+1}')), 'Q{q}')
                if q == 74:
                    addStringReport(get_answer('Q76'), 'Q76')
        
        if get_answers('Q31') in ['Q31_A3', 'Q31_A4']:
            report += "Storage / Attic:\n"
            for q in range(87, 93, 2):
                
                report += f"* {get_answer(f'Q{q}')} - {get_answer(f'Q{q+1}')}\n"
        
        if get_answers('Q32') in ['Q32_A1', 'Q32_A2', 'Q32_A3']:
            report += "Bathroom/shower/toilet:\n"
            for q in range(93, 106, 2):
                report += f"* {get_answer(f'Q{q}')} - {get_answer(f'Q{q+1}')}\n"
                if q == 95:
                    report += f": {get_answer('Q97')}\n"
                
        return report

    def generate_house_report(self, key_word):
        answers = AnswerQuestion.objects.all().filter(project=self)
        report = "<strong>Project type detalisation</strong>: \n"

        def answered(aid):
            nonlocal answers
            ans = answers.filter(answer__id=aid, project=self)
            return len(ans) > 0

        def get_answer(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            return ans[0].answer_text if ans else ""

        def get_answers(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            return [answer.answer_text for answer in ans]
        
        def addStringReport(string, qid):
            nonlocal report
            if get_answer(qid) == '':
                return
            else:
                report += string
                
        if answered('Q3_A1'):
            addStringReport("<strong>House refurbishment</strong>: * " + ", ".join(get_answers('Q5')), 'Q5')
            if answered('Q5_A3'):
                addStringReport(" <strong>Demolition Details</strong>: \n", 'Q6')
                addStringReport(self.formatPairAnswers(get_answers('Q6'),get_answers('Q7')), 'Q6')

        if answered('Q3_A2'):
            addStringReport(f"House extension: \n Extension type: {get_answer('Q11')}\n Roof type: {get_answer('Q12')}\n Extension Purposes: {', '.join(get_answers('Q13'))}\n\n", 'Q11')

        if answered('Q3_A3'):
            addStringReport(f"Loft Conversion: \n Conversion Type: {get_answer('Q14')}\n Conversion Purposes: {', '.join(get_answers('Q15'))}\n\n", 'Q14')

        if answered('Q3_A4'):
            addStringReport(f"Porch:\n Roof Type: {get_answer('Q16')}\n\n", 'Q16')

        if answered('Q3_A5'):
            addStringReport(f"Garage Conversion:\n Conversion type:\n {get_answer('Q17')} \nRoof type: {get_answer('Q18')} \n Conversion Purposes: {', '.join(get_answers('Q19'))}\n\n", 'Q17')

        if answered('Q3_A6'):
            addStringReport(f"Basement:\n Basement Purposes: {', '.join(get_answers('Q20'))}\n\n", 'Q20')

        if answered('Q3_A7'):
            addStringReport(f"Outbuilding: \n Type: {get_answer('Q21')} \n Roof type: {get_answer('Q22')} \n Outbuilding Purposes: {', '.join(get_answers('Q23'))}\n\n, 'Q21'")

        addStringReport("\nInternal Refurbishment detalisation:\n ", 'Q24')
        if answered('Q24_A2'):
            addStringReport("Not needed\n", 'Q24')
        elif answered('Q24_A1'):
            addStringReport("Number of Rooms to Refurbish on each Floor:\n ", 'Q26')
            addStringReport(self.formatPairAnswers(get_answers('Q26'),get_answers('Q27')), 'Q26')

        report += '\n\n'
        report += key_word

        addStringReport("\nExternal Refurbishment detalisation:\n", 'Q106')
        if answered('Q106_A2') in get_answers('Q106'):
            addStringReport("Not needed\n", 'Q106')
            
        elif answered('Q106_A1'):
            if answered('Q107_A1'):
                addStringReport("Exterior house surfaces:\n ", 'Q107')
                if answered('Q108_A1'):
                    addStringReport(f"Roof:\n Type: {get_answer('Q109')}\n Work:{get_answer('Q110')} \n Work details:{', '.join(get_answers('Q111'))} / {', '.join(get_answers('Q112'))}\n\n", 'Q109')
                if answered('Q108_A2'):
                    addStringReport(f"Front wall: Work: {get_answer('Q113')}\n Work details: {', '.join(get_answers('Q114'))} / {', '.join(get_answers('Q115'))}\n\n",'Q113')
                if answered('Q108_A3'):
                    addStringReport(f"Back wall:\n Work: {get_answer('Q116')} \n Work details: {', '.join(get_answers('Q117'))} / {', '.join(get_answers('Q118'))}\n\n", 'Q116')
                if answered('Q108_A4'):
                    addStringReport(f"Left hand side wall (facing the house) \nWork: {get_answer('Q119')} \nWork details: {', '.join(get_answers('Q120'))} / {', '.join(get_answers('Q121'))}\n\n", 'Q119')
                if answered('Q108_A5'):
                    addStringReport(f"Right hand side wall (facing the house) \nWork: {get_answer('Q122')} \nWork details: {', '.join(get_answers('Q123'))} / {', '.join(get_answers('Q124'))}\n\n", 'Q122')
                
                addStringReport("External Electrics:\n ", 'Q125')
                addStringReport(self.formatPairAnswers(get_answers('Q125'),get_answers('Q126')), 'Q125')
            
            if answered('Q107_A2'):
                addStringReport("Driveway:\n ", 'Q127')
                addStringReport(self.formatPairAnswers(get_answers('Q127'),get_answers('Q128')), 'Q127')
            if answered('Q107_A3'):
                addStringReport("Side passage:\n ", 'Q130')
                addStringReport(self.formatPairAnswers(get_answers('Q130'),get_answers('Q131')), 'Q130')
            if answered('Q107_A4'):
                addStringReport("Garden:\n ", 'Q133')
                addStringReport(self.formatPairAnswers(get_answers('Q133'),get_answers('Q134')), 'Q133')
                addStringReport(self.formatAnswers(get_answers('Q135')), 'Q135')
            if answered('Q107_A5'):
                addStringReport(f"\n{get_answer('Q107')}\n", 'Q107')
                
        return report
    @property
    def tree(self):
        
        def get_answers(question_instance_pk):
            answers = AnswerQuestion.objects.filter(question_instance=question_instance_pk, project=self)
            return [answer.answer_text for answer in answers]

        table = {
            'property_type':{
                'name':'Property type:',
                'text':''
            },
            'list_of_work':{
                'name':'List of work',
                'text':''
            },
            'project_type':{
                'name':'Project type',
                'text':''
            },
        }

        flat = True
        key_word = '[ROOMS]'
        current_room = 0

        def comparator_key(x):
            if x.qid == 'END':
                return 100000
            return int(x.qid[1:])

        for question in sorted(reversed(QuestionInstance.objects.all().filter(project=self)), key=comparator_key):
            if question.qid == 'Q2' or question.qid == 'Q1':
                table['property_type']['text'] += '<strong>' + ''.join(get_answers(question.pk)) + ' </strong>'
        
            if question.qid == 'Q1':
                answers = AnswerQuestion.objects.all().filter(question_instance=question.pk)

                for answer in answers:
                    if answer.answer.id == 'Q1_A1':
                        flat = True
                        table['project_type']['text'] += '<strong>Flat refurbishment</strong>' + '\n\n'
                    if answer.answer.id == 'Q1_A2':
                        flat = False
                        table['list_of_work']['text'] += self.generate_house_report(key_word)


            if question.qid  == 'Q3':
                if not flat:
                    answers = AnswerQuestion.objects.all().filter(question_instance=question.pk)
                    
                    for answer in answers:
                        table['project_type']['text'] += answer.answer_text + '\n'

            if question.qid == 'Q4':
                table['list_of_work']['text'] += '<strong>Project type detalisation:</strong> ' + ''.join(get_answers(question.pk)) + '\n\n'
            
            if question.qid == 'Q28':
                table['list_of_work']['text'] += '<strong>Refurbishment detalisation</strong>:\n    Number of Rooms to Refurbish: ' + ''.join(get_answers(question.pk)) + '\n\n'
            
            if question.qid == 'Q29':
                current_room += 1
                if flat:
                    table['list_of_work']['text'] += f'Room {current_room}:\n'
                    table['list_of_work']['text'] += self.generate_room_report(question.pk) + '\n\n'
                else:
                    ind =  table['list_of_work']['text'].find(key_word)
                    if ind:
                        table['list_of_work']['text'] = table['list_of_work']['text'][:ind+len(key_word)] + f'Room {current_room}:\n' +  self.generate_room_report(question.pk) + '\n\n' + table['list_of_work']['text'][ind+len(key_word):]
        table['list_of_work']['text'] = table['list_of_work']['text'].replace(key_word, '')
        return table


    @property
    def progress(self):
        question = QuestionInstance.objects.all().filter(project=self).last()
        if question.qid == 'END':
            return 100
        return round(int(question.qid.replace('Q',''))/len(Question.objects.all()) * 100)
    

    def deleteFromQueue(self, pk:str):
        queue = list(self.questions_queue.split(','))
        queue.remove(pk)
        self.questions_queue = ','.join(queue)
        return queue
    
    



    def get_current_question(self):
        current_question_id = list(self.questions_queue.strip().split(','))[0]
        current_question = QuestionInstance.objects.all().filter(pk=int(current_question_id))[0]
        return current_question

    def get_queue(self):
        return list(self.questions_queue.strip().split(','))
    
    def pushRight(self,  questionInstance):
        self.questions_queue = self.questions_queue  + str(questionInstance.pk) + ','
        return list(self.questions_queue.split(','))
    
    def pushLeft(self, questionInstance):
        self.questions_queue = ','.join([list(self.questions_queue.strip().split(','))[0]] + [str(questionInstance.pk)] + list(self.questions_queue.strip().split(','))[1:])
        return list(self.questions_queue.split(','))

    
    def pushAfterEquvalentQuestions(self, questionInstance):
        try:
            parent = QuestionInstance.objects.get(pk=questionInstance.parent_pk)
        except:
            return list(self.questions_queue.split(','))

        equvalent_questions = list(map(lambda x: x.pk, QuestionInstance.objects.all().filter(project=self, parent_pk=parent.parent_pk)))
        questions_queue = list(self.questions_queue.split(','))
        max_index = 0
        for i in range(len(questions_queue)):
            
            if questions_queue[i] != '' and int(questions_queue[i]) in equvalent_questions:
                max_index = i
        print('EQUVALENT',max_index, equvalent_questions, questions_queue)

        if max_index+2 < len(questions_queue):
            self.questions_queue = ','.join(questions_queue[0:max_index+1] + [str(questionInstance.pk)] + questions_queue[max_index+2:]) + ','
        else:
            self.questions_queue = ','.join(questions_queue[0:max_index+1] + [str(questionInstance.pk)]) + ','

        return list(self.questions_queue.split(','))

    def getNextQuestion(self):
        next_question = QuestionInstance.objects.get(pk=self.get_queue()[1])

        questions_queue = list(self.questions_queue.split(','))
        history_queue = list(self.history_queue.split(','))
        history_queue.append(questions_queue.pop(0))
        self.history_queue =  ','.join(history_queue)
        self.questions_queue = ','.join(questions_queue)
        self.save()
        print(next_question)
        return next_question
    
    def getNextQuestionInfo(self):
        return  QuestionInstance.objects.get(pk=self.get_queue()[1])



    def save(self, *args, **kwargs):
        print(self.pk)
        self.last_edit = timezone.now()
        if  len(QuestionInstance.objects.all().filter(project=self)) == 0:
            self.created = timezone.now()
        super(Project, self).save(*args, **kwargs)
        if  len(QuestionInstance.objects.all().filter(project=self)) == 0:
            q = QuestionInstance.objects.create(
                project=self,
                qid=Question.objects.get(id='Q1').id,
                parent=Question.objects.get(id='END'),
                text=Question.objects.get(id='Q1').text_template,
                parent_pk=0
            )  
            self.pushRight(q) 
            self.save()        
         
        



    


class QuestionInstance(models.Model):
    qid = models.CharField(_("question_id"), max_length=50)
    project =  models.ForeignKey(Project, verbose_name=_("project_id"), on_delete=models.CASCADE)
    params = models.CharField(_("params"), max_length=10000, default="{\"data\":[]}") #{data:['ans1', 'ans2']}
    parent =  models.ForeignKey(Question, verbose_name=_("parent_question"), on_delete=models.CASCADE)
    parent_pk =models.PositiveIntegerField(_("parent_pk"), max_length=50, default='')
    text = models.CharField(_("text"), max_length=1000)
    context = models.JSONField(_("context"),default=dict)
    
    
    def setContext(self, key, value):
        self.context[key] = value
        self.save()
    
    def getContext(self, key):
        
        try:
            return self.context[key]
        except:
            return ''
        
    def getParentQuestion(self, question:Question):
        instance = self
        while instance.parent_pk != 0:
            parent = QuestionInstance.objects.get(pk=instance.parent_pk)
            if parent.qid == question.id:
                return parent
            instance = parent
        if instance.qid == question.id:
            return instance
        return ValidationError('Don`t have parent for this question')
    
        
        
    
       

                
    def save(self, *args, **kwargs): 
        # print(self.params, self)
        # json_params = json.loads(self.params)
        # print(json_params)
        #check conditions
        
        conditions = NamingCondition.objects.filter(parent_question=Question.objects.get(id=self.qid))
        for condition in conditions:
            res = condition.evaluate(self)
            if res:
                self.text = res
        # update text
        if '[' in self.text:
            text  = self.text
            if '[Floor Name]' in text:
                text = text.replace('[Floor Name]', self.getContext('Floor Name'))
            if '[Room Sequence Number]' in text:
                text = text.replace('[Room Sequence Number]', self.getContext('Room Sequence Number'))
            parent_answer_pattern = re.compile(r'\[Q\d+\s+ANSWER\]')
            for match in parent_answer_pattern.finditer(text):
                parent_qid = match.group()[1:-8]
                try:
                    parent_question = self.getParentQuestion(Question.objects.get(id=parent_qid))
                    parent_answer = AnswerQuestion.objects.filter(
                        question_instance=parent_question.pk,
                        project=self.project
                    ).first()
                    if parent_answer:
                        text = text.replace(match.group(), parent_answer.answer_text)
                    else:
                        text = text.replace(match.group(), '')
                except Question.DoesNotExist:
                    print("QUESTION DOES NOT EXIST BY REPLACING IN QUESTION INSTANCE")
                    pass
            self.text = text

        super(QuestionInstance, self).save(*args, **kwargs)

        # if len(json_params['data']) > 0:
        #     self.text = self.text.format(*json_params['data'])






class AnswerQuestion(models.Model):
    answer = models.ForeignKey(Answer, verbose_name=_("answer_id"), on_delete=models.CASCADE)
    question_instance = models.PositiveIntegerField(_("question_instance"), max_length=50, default='')
    project = models.ForeignKey(Project, verbose_name=_("project_id"), on_delete=models.CASCADE)
    answer_text = models.CharField(_("answer_text"), max_length=300, default='')

    def addQuestionToQueue(self, questionInstance):
        if self.answer.conditions.find('insertion') != -1:
            json_conditions = json.loads(self.answer.conditions)
            insertion = json_conditions['insertion'].strip()
        else: insertion = 'Left'

        match insertion:
            case 'Right':
                self.project.pushRight(questionInstance)
            case 'Left':
                self.project.pushLeft(questionInstance)
            case 'After equvalent questions':
                self.project.pushAfterEquvalentQuestions(questionInstance)
        self.project.save()

        

    def checkConditions(self, *args, **kwargs):
        if self.answer.conditions.find('conditions') != -1:
            json_conditions = json.loads(self.answer.conditions)
            conditions = json_conditions['conditions'].strip()
        else: conditions = ''
        try:
            if len(conditions) > 0:
                for condition in conditions.split(';'):
                    result = condition.split(':')[1].strip()
                    body = list(map(lambda x: x.strip(), condition.split('(')[1].split(')')[0].strip().split(',')))
                    
                    type_condition = body[-1]
                    body.pop()

                    elements = []

                    for el in body:
                        if 'ANSWER' in el:
                            for i in  AnswerQuestion.objects.filter(project=self.project):
                                if i.answer.question.id == el.split('_')[1]:
                                    elements.append(i.answer.id)
                        elif 'PARENT' in el:
                            try:
                                parent_id = QuestionInstance.objects.get(question__qid=el.split('_')[1]).parent.id
                                elements.append(parent_id)
                            except: print(f'Parent question not found!\n{conditions}')
                        else:
                            elements.append(el)
                        

                    match type_condition:
                        case 'EQUAL':
                            for el in elements[:-1]:
                                if el == elements[-1]:
                                    return result
                            
                        case 'NOTEQUAL':
                            flag = True

                            for el in elements[:-1]:
                                if el == elements[-1]:
                                    flag = False
                                    break
                            if flag:
                                return result
                        case 'ANSWERED_ALL':
                            flag = 0
                            for el in elements:
                                answered = AnswerQuestion.objects.filter(answer__id=el)
                                if len(answered) > 0:
                                    flag += 1
                            if flag == len(elements):
                                return result

                        case 'ANSWERED_ANY':
                            for el in elements:
                                answered = AnswerQuestion.objects.filter(answer__id=el)
                                if len(answered) > 0:
                                    return result
        except Exception as e: 
            print('!!!!CHECK CONDITIONS ERRROR!!!!!!!', e)
            return self.answer.next_id
        return self.answer.next_id

    def save(self, *args, **kwargs):
        new_question = []
        print(self.answer.type)

        if self.answer.conditions.find('params') != -1:
            json_conditions = json.loads(self.answer.conditions)
            params = json_conditions['params']
        else: params = ''

        next_id = self.checkConditions()

        if next_id == 'NEXT':
            next_id = self.project.getNextQuestionInfo()
        
        print('NEXTID', next_id, 'PARENT_PK', self.question_instance)

        parentContext = QuestionInstance.objects.get(pk=self.question_instance).context

        match self.answer.type.strip():
            case AnswerTypes.CUSTOM:
                question_template = Question.objects.get(id=next_id)
                new_question.append(QuestionInstance.objects.create(
                    qid=question_template.id,
                    text=question_template.text_template,
                    project=self.project,
                    params='{"data":' + json.dumps(params) + '}',
                    parent=self.answer.question,
                    parent_pk= self.question_instance,
                    context=parentContext,
                ))

            case AnswerTypes.SINGLE:

                question_template = Question.objects.get(id=next_id)
               
                print(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance))

                if len(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance)) == 0:
                     new_question.append(QuestionInstance.objects.create(
                        qid=question_template.id,
                        text=question_template.text_template,
                        project=self.project,
                        params='{"data":' + json.dumps(params) + '}',
                        parent=self.answer.question,
                        parent_pk= self.question_instance,
                        context=parentContext,
                    ))
            case AnswerTypes.NQONE:
                print(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance))
                question_template = Question.objects.get(id=next_id)
                if len(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance)) == 0:
                     new_question.append(QuestionInstance.objects.create(
                        qid=question_template.id,
                        text=question_template.text_template,
                        project=self.project,
                        params='{"data":' + json.dumps(params) + '}',
                        parent=self.answer.question,
                        parent_pk= self.question_instance,
                        context=parentContext,
                    ))
            case AnswerTypes.NQEACH:
                question_template = Question.objects.get(id=next_id)
                if next_id == 'Q27':
                    parentContext['Floor Name'] = self.answer_text
                new_question.append(QuestionInstance.objects.create(
                    qid=question_template.id,
                    text=question_template.text_template,
                    project=self.project,
                    params='{"data":' + json.dumps(params) + '}',
                    parent_pk= self.question_instance,
                    parent=self.answer.question,
                    context=parentContext,
                ))
            case AnswerTypes.NUMBEREACH:
                for i in range(int(self.answer_text)):
                    print(next_id)
                    question_template = Question.objects.get(id=next_id)
                    localContext = parentContext
                    localContext.update({"Room Sequence Number":str(i+1)})
                    local_new_question = QuestionInstance.objects.create(
                        qid=question_template.id,
                        text=question_template.text_template,
                        project=self.project,
                        params='{"data":["' + str(i) + '"]}',
                        parent=self.answer.question,
                        parent_pk=self.question_instance,
                        context=localContext,
                    )
                    
                    new_question.append(local_new_question)
        print('NEW QUESTIONS', new_question)
        if len(new_question) > 0:
            for question in new_question:
                self.addQuestionToQueue(question)
        super(AnswerQuestion, self).save(*args, **kwargs)


class NamingCondition(models.Model):
    parent_question = models.ForeignKey(Question,related_name='parent_question', verbose_name=_("Parent Question"), on_delete=models.CASCADE)
    left_operand = models.ForeignKey(Question,related_name='left_operand',  verbose_name=_("Question Answers"), on_delete=models.CASCADE)
    condition_type = models.CharField(_("Condition Type"), max_length=50, choices=ConditionTypes.choices)
    right_operand = models.ManyToManyField(Answer, verbose_name=_("Answers"), blank=True)
    text_template = models.CharField(_("Text template"), max_length=1000, default='')
    def __str__(self):
        return f"{self.parent_question}: {self.left_operand} {self.condition_type} {self.right_operand}"

    def getParentQuestion(self,questionInstance:QuestionInstance,  question:Question):
        instance = questionInstance
        while instance.parent_pk != 0:
            parent = QuestionInstance.objects.get(pk=instance.parent_pk)
            if parent.qid == question.id:
                return parent
            instance = parent
        if instance.qid == question.id:
            return instance
        return ValidationError('Don`t have parent for this question')
            
    def evaluate(self, questionInstance:QuestionInstance):
        parent = self.getParentQuestion(questionInstance, self.left_operand)
        left_value = list(map(lambda answer: answer.answer_text, AnswerQuestion.objects.filter(question_instance=parent.pk)))
        right_value = list(map(lambda answer:answer.text, self.right_operand.all()))        
        
        
        if self.condition_type == 'EQUAL':
            for answer in left_value:
                if answer not in right_value:
                    return False
            return self.text_template
        
        elif self.condition_type == 'NOT_EQUAL':
            for answer in left_value:
                if answer not in right_value:
                    return self.text_template
            return False
        else:
            raise ValidationError(f"Unknown condition type: {self.condition_type}")




