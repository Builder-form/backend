from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import json
from django.utils import timezone
from user.models import User
from django.core.exceptions import ValidationError
from collections import defaultdict
import re
from django.contrib.auth.models import Group

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
    

class APPSettings(models.Model):
    cost = models.PositiveIntegerField(_("Cost of one purchase"), default=10)
    projects_per_purchase = models.PositiveBigIntegerField(_('Projects per one purchase'), default=1)
    isActive = models.BooleanField(_('Is Active'), default=False)
    

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
    answered_questions = models.PositiveIntegerField(_("Answered questions"), default=0, blank=True)
    short_description = models.CharField(_("Short description"), max_length=10000, default='', blank=True)

    def normalize_history_or_queue(self, history_or_queue_list):
        while '' in history_or_queue_list:
            history_or_queue_list.remove('')
        while ' ' in history_or_queue_list:
            history_or_queue_list.remove(' ')
        return history_or_queue_list

    def back(self):
        current_question = self.get_current_question()
        self.deleteFromQueue(str(current_question.pk))
        current_question.delete()

        history = list(self.history_queue.split(','))
        self.normalize_history_or_queue(history)
        
        last_answered_question_instance = QuestionInstance.objects.get(pk=history[-1])
        history.pop()

        last_question_instance_childrens = QuestionInstance.objects.filter(parent_pk=last_answered_question_instance.pk)
        # print(last_question_instance_childrens)
        for child in last_question_instance_childrens:
            try: 
                history.remove(child.pk)
            except:
                pass
            try:
                self.deleteFromQueue(str(child.pk))
            except:
                pass

        last_question_instance_childrens.delete()


        last_answered_question = Question.objects.get(id=last_answered_question_instance.qid)
        AnswerQuestion.objects.all().filter(answer__question=last_answered_question).delete()

        
        self.history_queue = ','.join(history)
        self.questions_queue =  str(last_answered_question_instance.pk) + ',' + self.questions_queue

        self.save()

        return last_answered_question_instance  

    def formatAnswers(self, answers):
        a = ''
        for ans in answers:
            a+=f"<div>&emsp;- {ans}<br/></div>"
        return a
        
    def formatPairAnswers(self, answers1, answers2):
        result = ''
        if len(answers1) == 0 and len(answers2) == 0:
            return result
        for i in range(len(answers1)):
            ans2 = '- ' + answers2[i] if i < len(answers2) else ''
            result += f'<div>&emsp;- {answers1[i]} {ans2}</div><br/>'
        return result
    
    def get_answers_tree(self, qid, parent_pk):
        answers = AnswerQuestion.objects.filter(project=self)
        ans = answers.filter(answer__question__id=qid)

        # print('PARENT_PK',ans, parent_pk)

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

        def get_answer_text(list_qid):
            return [Answer.objects.get(id=qid).text for qid in list_qid]
        
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
        if len(get_answers('Q30')) == 0 and len(get_answers('Q31')) == 0 and len(get_answers('Q32')) == 0:
            return ''
        report += f"<strong>Room purposes</strong>: {', '.join(get_answers('Q30'))}  {', '.join(get_answers('Q31'))}  {', '.join(get_answers('Q32'))} <br/>"
        
        report += "<strong><u>Strip out and demolition</u></strong>:<br/>"
        report += "<strong>Room type specific:</strong><br/>"

        for q in range(34, 46, 2):
            addStringReport(self.formatPairAnswers(get_answers(f'Q{q}'), get_answers(f'Q{q+1}')) , f'Q{q}')
        
        addStringReport("<strong>Ceilings:</strong><br/>", 'Q46')
        addStringReport(self.formatAnswers(get_answers('Q46')), 'Q46')

        addStringReport("<strong>Walls:</strong><br/>", 'Q47')
        addStringReport(self.formatPairAnswers(get_answers('Q47'),get_answers('Q48')), 'Q47')

        addStringReport("<strong>Floors:</strong><br/>", 'Q49')
        addStringReport(self.formatPairAnswers(get_answers('Q49'),get_answers('Q50')), 'Q49')

        addStringReport("<br/><strong><u>Structure improvement:<br/></u></strong>", 'Q52')
        addStringReport("<strong>Ceilings:</strong><br/>", 'Q52')
        addStringReport(self.formatAnswers(get_answers('Q52')), 'Q52')

        addStringReport("<strong>Walls:</strong><br/>", 'Q53')
        addStringReport(self.formatAnswers(get_answers('Q53')), 'Q53')

        addStringReport("<strong>Floors:</strong><br/>", 'Q54')
        addStringReport(self.formatAnswers(get_answers('Q54')), 'Q54')
        
        addStringReport("<br/><strong><u>Internal decoration and finishes:<br/></u></strong>", 'Q56')
        addStringReport("<strong>Ceilings:</strong><br/>", 'Q56')
        addStringReport(self.formatAnswers(get_answers('Q56')), 'Q56')

        addStringReport("<strong>Walls:</strong><br/>", 'Q57')
        addStringReport(self.formatPairAnswers(get_answers('Q57'),get_answers('Q58')), 'Q57')

        addStringReport("<strong>Floors:</strong><br/>", 'Q59')
        addStringReport(self.formatPairAnswers(get_answers('Q59'),get_answers('Q60')), 'Q59')
        
        addStringReport("<strong>Woodwork:</strong><br/>", 'Q61')
        addStringReport(self.formatAnswers(get_answers('Q61')), 'Q61')

        addStringReport("<br/><strong><u>Fitting and installing:<br/></u></strong>", 'Q63')
        addStringReport("<strong>Windows:</strong><br/>", 'Q63')
        addStringReport(self.formatPairAnswers(get_answers('Q63'),get_answers('Q64')), 'Q63')

        addStringReport("<strong>External doors:</strong><br/>", 'Q641')
        addStringReport(self.formatPairAnswers(get_answers('Q641'),get_answers('Q642')), 'Q641')

        addStringReport("<strong>Internal doors:</strong><br/>", 'Q65')
        addStringReport(self.formatPairAnswers(get_answers('Q65'),get_answers('Q66')), 'Q65')

        addStringReport("<strong>Inside rooms/hallway/landings:</strong><br/>", 'Q67')
        addStringReport(self.formatPairAnswers(get_answers('Q67'),get_answers('Q68')), 'Q67')

        addStringReport("<strong>Electrics:</strong><br/>", 'Q69')
        addStringReport(self.formatPairAnswers(get_answers('Q69'),get_answers('Q691')), 'Q69')

        print('Q31 ANWERS', get_answers('Q31'), get_answer_text(['Q31_A1', 'Q31_A2', 'Q31_A3', 'Q31_A4']))
        if any(ans in get_answer_text(['Q31_A1', 'Q31_A2']) for ans in get_answers('Q31')):
            report += "Room type specific:<br/>"
            report += "Kitchen / Ulitity:<br/>"
            for q in range(70, 87, 2):
                addStringReport(self.formatPairAnswers(get_answers(f'Q{q}'), get_answers(f'Q{q+1}')), f'Q{q}')
                if q == 74:
                    addStringReport(get_answer('Q76'), 'Q76')
        
        if any(ans in get_answer_text(['Q31_A3', 'Q31_A4']) for ans in get_answers('Q31')):
            report += "Storage / Attic:<br/>"
            for q in range(87, 93, 2):
                addStringReport(self.formatPairAnswers(get_answers(f'Q{q}'), get_answers(f'Q{q+1}')), f'Q{q}')
        
        if any(ans in get_answer_text(['Q32_A1', 'Q32_A2', 'Q32_A3']) for ans in get_answers('Q32')):
            report += "Bathroom/shower/toilet:<br/>"
            for q in range(93, 106, 2):
                addStringReport(self.formatPairAnswers(get_answers(f'Q{q}'), get_answers(f'Q{q+1}')), f'Q{q}')
                if q == 95:
                    addStringReport(get_answer('Q97'), 'Q97')
                
        return report

    def generate_house_report(self, key_word):
        answers = AnswerQuestion.objects.all().filter(project=self)
        report = "<strong>Project type detalisation</strong>: <br/>"

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
            addStringReport("<strong>House refurbishment</strong>: - " + ", ".join(get_answers('Q5')), 'Q5')
            if answered('Q5_A3'):
                addStringReport(" <strong>Demolition Details</strong>: <br/>", 'Q6')
                addStringReport(self.formatPairAnswers(get_answers('Q6'),get_answers('Q7')), 'Q6')

        if answered('Q3_A2'):
            addStringReport(f"House extension: <br/> Extension type: {get_answer('Q11')}<br/> Roof type: {get_answer('Q12')}<br/> Extension Purposes: {', '.join(get_answers('Q13'))}<br/>", 'Q11')

        if answered('Q3_A3'):
            addStringReport(f"Loft Conversion: <br/> Conversion Type: {get_answer('Q14')}<br/> Conversion Purposes: {', '.join(get_answers('Q15'))}<br/>", 'Q14')

        if answered('Q3_A4'):
            addStringReport(f"Porch:<br/> Roof Type: {get_answer('Q16')}<br/>", 'Q16')

        if answered('Q3_A5'):
            addStringReport(f"Garage Conversion:<br/> Conversion type:<br/> {get_answer('Q17')} <br/>Roof type: {get_answer('Q18')} <br/> Conversion Purposes: {', '.join(get_answers('Q19'))}<br/>", 'Q17')

        if answered('Q3_A6'):
            addStringReport(f"Basement:<br/> Basement Purposes: {', '.join(get_answers('Q20'))}<br/>", 'Q20')

        if answered('Q3_A7'):
            addStringReport(f"Outbuilding: <br/> Type: {get_answer('Q21')} <br/> Roof type: {get_answer('Q22')} <br/> Outbuilding Purposes: {', '.join(get_answers('Q23'))}<br/>, 'Q21'")

        addStringReport("<br/>Internal Refurbishment detalisation:<br/> ", 'Q24')
        if answered('Q24_A2'):
            addStringReport("Not needed<br/>", 'Q24')
        elif answered('Q24_A1'):
            addStringReport("Number of Rooms to Refurbish on each Floor:<br/> ", 'Q26')
            addStringReport(self.formatPairAnswers(get_answers('Q26'),get_answers('Q27')), 'Q26')

        report += '<br/>'
        report += key_word

        addStringReport("<br/>External Refurbishment detalisation:<br/>", 'Q106')
        if answered('Q106_A2') in get_answers('Q106'):
            addStringReport("Not needed<br/>", 'Q106')
            
        elif answered('Q106_A1'):
            if answered('Q107_A1'):
                addStringReport("Exterior house surfaces:<br/> ", 'Q107')
                if answered('Q108_A1'):
                    addStringReport(f"Roof:<br/> Type: {get_answer('Q109')}<br/> Work:{get_answer('Q110')} <br/> Work details:{', '.join(get_answers('Q111'))} / {', '.join(get_answers('Q112'))}<br/>", 'Q109')
                if answered('Q108_A2'):
                    addStringReport(f"Front wall: Work: {get_answer('Q113')}<br/> Work details: {', '.join(get_answers('Q114'))} / {', '.join(get_answers('Q115'))}<br/>",'Q113')
                if answered('Q108_A3'):
                    addStringReport(f"Back wall:<br/> Work: {get_answer('Q116')} <br/> Work details: {', '.join(get_answers('Q117'))} / {', '.join(get_answers('Q118'))}<br/>", 'Q116')
                if answered('Q108_A4'):
                    addStringReport(f"Left hand side wall (facing the house) <br/>Work: {get_answer('Q119')} <br/>Work details: {', '.join(get_answers('Q120'))} / {', '.join(get_answers('Q121'))}<br/>", 'Q119')
                if answered('Q108_A5'):
                    addStringReport(f"Right hand side wall (facing the house) <br/>Work: {get_answer('Q122')} <br/>Work details: {', '.join(get_answers('Q123'))} / {', '.join(get_answers('Q124'))}<br/>", 'Q122')
                
                addStringReport("External Electrics:<br/> ", 'Q125')
                addStringReport(self.formatPairAnswers(get_answers('Q125'),get_answers('Q126')), 'Q125')
            
            if answered('Q107_A2'):
                addStringReport("Driveway:<br/> ", 'Q127')
                addStringReport(self.formatPairAnswers(get_answers('Q127'),get_answers('Q128')), 'Q127')
            if answered('Q107_A3'):
                addStringReport("Side passage:<br/> ", 'Q130')
                addStringReport(self.formatPairAnswers(get_answers('Q130'),get_answers('Q131')), 'Q130')
            if answered('Q107_A4'):
                addStringReport("Garden:<br/> ", 'Q133')
                addStringReport(self.formatPairAnswers(get_answers('Q133'),get_answers('Q134')), 'Q133')
                addStringReport(self.formatAnswers(get_answers('Q135')), 'Q135')
            if answered('Q107_A5'):
                addStringReport(f"<br/>{get_answer('Q107')}<br/>", 'Q107')
                
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
                    if answer.answer.id == 'Q1_A2':
                        flat = True
                        table['project_type']['text'] += '<strong>Flat refurbishment</strong>' + '<br/>'
                    if answer.answer.id == 'Q1_A1':
                        flat = False
                        table['list_of_work']['text'] += self.generate_house_report(key_word)


            if question.qid  == 'Q3':
                if not flat:
                    answers = AnswerQuestion.objects.all().filter(question_instance=question.pk)
                    
                    for answer in answers:
                        table['project_type']['text'] += answer.answer_text + '<br/>'

            if question.qid == 'Q4':
                # table['list_of_work']['text'] += '<strong>Project type detalisation:</strong> ' + ''.join(get_answers(question.pk)) + '<br/>'
                table['list_of_work']['text'] +=  ''.join(get_answers(question.pk)) + '<br/>'

            if question.qid == 'Q28':
                # table['list_of_work']['text'] += '<strong>Refurbishment detalisation:</strong><br/>    Number of Rooms to Refurbish: ' + ''.join(get_answers(question.pk)) + '<br/>'
                table['list_of_work']['text'] += 'Number of Rooms to Refurbish: ' + ''.join(get_answers(question.pk)) + '<br/>'

            if question.qid == 'Q29' and self:
                current_room += 1
                # print("LEN_TREE", question.pk, self.get_answers_tree('Q30', question.pk), self.get_answers_tree('Q31', question.pk), self.get_answers_tree('Q32', question.pk))
                if len(self.get_answers_tree('Q30', question.pk)) == 0 and len(self.get_answers_tree('Q31', question.pk)) == 0 and len(self.get_answers_tree('Q32', question.pk)) == 0:
                    continue

                if flat:
                    table['list_of_work']['text'] += f'Room {current_room}:<br/>'
                    table['list_of_work']['text'] += self.generate_room_report(question.pk) + '<br/>'
                else:
                    ind =  table['list_of_work']['text'].find(key_word)
                    if ind:
                        table['list_of_work']['text'] = table['list_of_work']['text'][:ind+len(key_word)] + f'Room {current_room}:<br/>' +  self.generate_room_report(question.pk) + '<br/>' + table['list_of_work']['text'][ind+len(key_word):]
        table['list_of_work']['text'] = table['list_of_work']['text'].replace(key_word, '')
        table['list_of_work']['text'] = re.sub(r'(?:<br/>)+$', '', table['list_of_work']['text'])
        return table

    @property
    def progress(self):
        # print('HISTORY_QUEUE', self.history_queue)
        if len(self.history_queue.split(',')) > 1:
            question = QuestionInstance.objects.filter(pk__in=self.history_queue.split(',')).order_by('-qid').first()
        else:
            return 1
        
        check_end_question = QuestionInstance.objects.get(pk=list(self.questions_queue.split(','))[0])
        if check_end_question.text == 'END':
            return 100
        
        numerator = int(question.qid.replace('Q',''))
        if numerator > len(Question.objects.all()):
            numerator = int(question.qid.replace('Q','')[:-1])
        
        denominator = len(Question.objects.all())
        return round(numerator/denominator * 100)
    
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
        self.questions_queue = ','.join(self.normalize_history_or_queue(list(self.questions_queue.split(',')))) + ','
        return list(self.questions_queue.split(','))
    
    def pushLeft(self, questionInstance):
        self.questions_queue = ','.join([list(self.questions_queue.strip().split(','))[0]] + [str(questionInstance.pk)] + list(self.questions_queue.strip().split(','))[1:])
        self.questions_queue = ','.join(self.normalize_history_or_queue(list(self.questions_queue.split(',')))) + ','
        return list(self.questions_queue.split(','))
    
    def get_recursive_children_in_queue(self, instance):
        children_eq = []
        children = QuestionInstance.objects.filter(project=self, parent_pk=instance.pk)
        for child in children:
            if str(child.pk) in self.questions_queue:
                children_eq.append(child.pk)
            children_eq.extend(self.get_recursive_children_in_queue(child))
        return children_eq
    
    def pushAfterEquvalentQuestions(self, questionInstance):
        try:
            parent = QuestionInstance.objects.get(pk=questionInstance.parent_pk)
        except:
            return list(self.questions_queue.split(','))
        


        current = parent
        equivalent_questions = []
        list_of_questions = list(self.questions_queue.split(','))
        while current.parent_pk != 0:
            siblings = QuestionInstance.objects.filter(project=self, parent_pk=current.parent_pk)
            # print('SIBLINGS', siblings)
            if siblings.count() > 1:
                equivalent_questions = []
                for s in siblings:
                    if str(s.pk) in self.questions_queue:
                        equivalent_questions.append(s.pk)
                    equivalent_questions.extend(self.get_recursive_children_in_queue(s))
                break
            try:
                current = QuestionInstance.objects.get(pk=current.parent_pk)
            except QuestionInstance.DoesNotExist:
                break
        
        # print('EQUIVALENT_QUESTIONS', equivalent_questions)
        list_of_questions = self.normalize_history_or_queue(list_of_questions)

        if equivalent_questions:
            last_equiv_index = max([list_of_questions.index(str(pk)) for pk in equivalent_questions])
            if last_equiv_index + 1 < len(list_of_questions):
                first_after_equiv = QuestionInstance.objects.get(pk=list_of_questions[last_equiv_index + 1])
                # print('FIRST_AFTER_EQUIV', first_after_equiv.pk, questionInstance.pk)
                if questionInstance.parent == first_after_equiv.parent and questionInstance.text == first_after_equiv.text:
                    questionInstance.delete()
                    return list(self.questions_queue.split(','))
            self.questions_queue = ','.join(list_of_questions[:last_equiv_index + 1] + [str(questionInstance.pk)] + list_of_questions[last_equiv_index + 1:]) + ','
        else:
            self.pushLeft(questionInstance)

        # equvalent_questions = list(map(lambda x: x.pk, QuestionInstance.objects.all().filter(project=self, pk=parent.parent_pk)))
        # questions_queue = list(self.questions_queue.split(','))
        # max_index = 0

        # for i in range(len(questions_queue)):
        #     if questions_queue[i] != '' and int(questions_queue[i]) in equvalent_questions:
        #         max_index = i
    
        # print('EQUVALENT',max_index, equvalent_questions, questions_queue, QuestionInstance.objects.all().filter(project=self, parent_pk=parent.parent_pk), parent.parent_pk)
        # print("EQUVALENT2", QuestionInstance.objects.all().filter(project=self, parent_pk=parent.parent_pk), parent.parent_pk)
        # if max_index+1 < len(questions_queue):
        #     self.questions_queue = ','.join(questions_queue[0:max_index+1] + [str(questionInstance.pk)] + questions_queue[max_index+1:]) + ','
        # else:
        #     self.questions_queue = ','.join(questions_queue[0:max_index+1] + [str(questionInstance.pk)]) + ','

        self.questions_queue = ','.join(self.normalize_history_or_queue(list(self.questions_queue.split(',')))) + ','
        return list(self.questions_queue.split(','))

    def getNextQuestion(self):
        next_question = QuestionInstance.objects.get(pk=self.get_queue()[1])

        questions_queue = list(self.questions_queue.split(','))
        history_queue = list(self.history_queue.split(','))
        history_queue.append(questions_queue.pop(0))
        self.history_queue =  ','.join(self.normalize_history_or_queue(history_queue))
        self.questions_queue = ','.join(questions_queue)
        self.save()
        # print(next_question)
        return next_question
    
    def getNextQuestionInfo(self):
        return  QuestionInstance.objects.get(pk=self.get_queue()[1])

    def save(self, *args, **kwargs):
        self.last_edit = timezone.now()
        questions = QuestionInstance.objects.all().filter(project=self)
        # if len(self.history_queue.split(',')) > 1:
        if len(self.history_queue.split(',')) > 1 and  int(QuestionInstance.objects.get(pk=self.history_queue.split(',')[-1]).qid[1:]) < 10:
            description = ""
            answered_questions = AnswerQuestion.objects.filter(project=self)

            question_answers = defaultdict(list)
            for aq in answered_questions:
                question = aq.answer.question
                question_answers[question.id].append(aq.answer.text)
            # print('ANSWERED_QUESTIONS', question_answers, answered_questions)
            sorted_questions = sorted(question_answers.items(), key=lambda x: int(x[0][1:]))

            for qid, answers in sorted_questions:
                if int(qid[1:]) < 10:
                    question_text = answered_questions.filter(answer__question__id=qid).first().answer.question.text_template
                    description += f"<strong>{question_text}</strong><br/>"
                    for answer in answers:
                        description += f"&emsp;- {answer}<br/>"
            # print("DESCRIPTION", description)
            self.short_description = description
            

        if len(questions) == 0:
            self.created = timezone.now()
        super(Project, self).save(*args, **kwargs)
        if  len(questions) == 0:
            q = QuestionInstance.objects.create(
                project=self,
                qid=Question.objects.get(id='Q1').id,
                parent=Question.objects.get(id='END'),
                text=Question.objects.get(id='Q1').text_template,
                parent_pk=0,
                parent_answer_pk=0,
            )  
            self.pushRight(q) 
            self.save()        
         
        



    


class QuestionInstance(models.Model):
    qid = models.CharField(_("question_id"), max_length=50)
    project =  models.ForeignKey(Project, verbose_name=_("project_id"), on_delete=models.CASCADE)
    params = models.CharField(_("params"), max_length=10000, default="{\"data\":[]}") #{data:['ans1', 'ans2']}
    parent =  models.ForeignKey(Question, verbose_name=_("parent_question"), on_delete=models.CASCADE)
    parent_answer_pk = models.PositiveIntegerField(_("parent_answer_pk"), max_length=50, default=0, null=True, blank=True)
    parent_pk = models.PositiveIntegerField(_("parent_pk"), max_length=50, default=0)
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
    
    def getParentAnswer(self, question:Question):
        instance = self
        while instance.parent_answer_pk != 0:
            parent_answer = AnswerQuestion.objects.get(pk=instance.parent_answer_pk)
            if parent_answer.answer.question.id == question.id:
                return parent_answer
            instance = parent_answer
        return ValidationError('Don`t have parent_answer for this question')
                    
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
                text = text.replace('[Room Sequence Number]', 'Room №' + self.getContext('Room Sequence Number'))
            
            parent_answer_pattern = re.compile(r'\[Q\d{1,4}\s+[Aa][Nn][Ss][Ww][Ee][Rr]\]')
            for match in parent_answer_pattern.finditer(text):
                parent_qid = match.group()[1:-8]
                try:
                    # parent_question = self.getParentQuestion(Question.objects.get(id=parent_qid))
                    parent_answer = self.getParentAnswer(Question.objects.get(id=parent_qid))
                    if parent_answer:
                        text = text.replace(match.group(), parent_answer.answer_text)
                    else:
                        text = text.replace(match.group(), '')
                except Question.DoesNotExist:
                    print("QUESTION DOES NOT EXIST BY REPLACING IN QUESTION INSTANCE")
                    pass
            self.text = text

        super(QuestionInstance, self).save(*args, **kwargs)


class AnswerQuestion(models.Model):
    answer = models.ForeignKey(Answer, verbose_name=_("answer_id"), on_delete=models.CASCADE)
    question_instance = models.PositiveIntegerField(_("question_instance"), max_length=50, default='')
    project = models.ForeignKey(Project, verbose_name=_("project_id"), on_delete=models.CASCADE)
    answer_text = models.CharField(_("answer_text"), max_length=300, default='')

    def addQuestionToQueue(self, questionInstance):
        if questionInstance.text == 'END':
            self.project.pushRight(questionInstance)
            self.project.save()
            return
        
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
        else:
            conditions = ''
        try:
            # Получаем список идентификаторов предков текущего QuestionInstance
            ancestor_ids = []
            try:
                current_instance = QuestionInstance.objects.get(pk=self.question_instance)
                while current_instance.parent_pk:
                    try:
                        current_instance = QuestionInstance.objects.get(pk=current_instance.parent_pk)
                        ancestor_ids.append(current_instance.pk)
                    except QuestionInstance.DoesNotExist:
                        break
            except Exception as e:
                print("Ошибка при получении предков:", e)

            if len(conditions) > 0:
                for condition in conditions.split(';'):
                    if not condition.strip():
                        continue
                    result = condition.split(':')[1].strip()
                    body = list(
                        map(lambda x: x.strip(), 
                            condition.split('(')[1].split(')')[0].strip().split(',')
                        )
                    )
                    
                    type_condition = body[-1]
                    body.pop()

                    elements = []

                    print(body, type_condition)

                    for el in body:
                        if 'ANSWER' in el:
                            # Искать среди ответов, принадлежащих предкам
                            for i in AnswerQuestion.objects.filter(
                                project=self.project,
                                question_instance__in=ancestor_ids
                            ):
                                if i.answer.question.id == el.split('_')[1]:
                                    elements.append(i.answer.id)
                        elif 'PARENT' in el:
                            try:
                                # Поиск родительского вопроса только среди предков
                                parent_instance = QuestionInstance.objects.filter(
                                    pk__in=ancestor_ids,
                                    question__qid=el.split('_')[1]
                                ).first()
                                if parent_instance:
                                    elements.append(parent_instance.parent.id)
                            except Exception as e:
                                print(f'Родительский вопрос не найден!<br/>{conditions}: {e}')
                        else:
                            elements.append(el)
                    
                    print('ELEMENTS', elements)

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
                                answered = AnswerQuestion.objects.filter(
                                    answer__id=el,
                                    question_instance__in=ancestor_ids
                                )
                                if answered.exists():
                                    flag += 1
                            if flag == len(elements):
                                return result
                        case 'ANSWERED_ANY':
                            for el in elements:
                                answered = AnswerQuestion.objects.filter(
                                    answer__id=el,
                                    question_instance__in=ancestor_ids
                                )
                                if answered.exists():
                                    return result
                        case 'EXIST_SUPPLY':
                            siblings = QuestionInstance.objects.filter(
                                project=self.project,
                                parent_pk=QuestionInstance.objects.get(pk=self.question_instance).parent_pk
                            )

                            cnt = 0
                            for sibling in siblings:
                                if sibling.qid == self.answer.next_id: # значит что отец создал вопрос (пример с remove to dispose)
                                    return result
                                try:
                                    cnt += QuestionInstance.objects.filter(
                                    project=self.project,
                                    parent_pk=sibling.pk,
                                ).count()
                                except:
                                    pass
                            if cnt > 0:
                                return result
        except Exception as e: 
            print('!!!!CHECK CONDITIONS ERROR!!!!!!!', e)
            return self.answer.next_id
        return self.answer.next_id

    def save(self, *args, **kwargs):
        super(AnswerQuestion, self).save(*args, **kwargs)
        if not getattr(self, '_creating_related', False):
            self._creating_related = True

            try: 
                new_question = []
                # print(self.answer.type)

                if self.answer.conditions.find('params') != -1:
                    json_conditions = json.loads(self.answer.conditions)
                    params = json_conditions['params']
                else: params = ''

                next_id = self.checkConditions()

                if next_id == 'SKIP':
                    return
                if next_id == 'NEXT':
                    next_id = self.project.getNextQuestionInfo()
                

                # print('NEXTID', next_id, 'PARENT_PK', self.question_instance)

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
                            parent_answer_pk= self.pk,

                        ))

                    case AnswerTypes.SINGLE:

                        question_template = Question.objects.get(id=next_id)

                        # print(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance))

                        if len(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance)) == 0:
                            new_question.append(QuestionInstance.objects.create(
                                qid=question_template.id,
                                text=question_template.text_template,
                                project=self.project,
                                params='{"data":' + json.dumps(params) + '}',
                                parent=self.answer.question,
                                parent_pk= self.question_instance,
                                context=parentContext,
                                parent_answer_pk= self.pk,
                            ))
                    case AnswerTypes.NQONE:
                        # print(QuestionInstance.objects.all().filter(project=self.project).filter(parent_pk=self.question_instance))
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
                                parent_answer_pk= self.pk,
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
                            parent_answer_pk= self.pk,
                        ))
                    case AnswerTypes.NUMBEREACH:
                        for i in range(int(self.answer_text), 0, -1):
                            # print('ITER', i,next_id)
                            question_template = Question.objects.get(id=next_id)
                            localContext = parentContext
                            localContext.update({"Room Sequence Number":str(i)})
                            local_new_question = QuestionInstance.objects.create(
                                qid=question_template.id,
                                text=question_template.text_template,
                                project=self.project,
                                params='{"data":["' + str(i) + '"]}',
                                parent=self.answer.question,
                                parent_pk=self.question_instance,
                                context=localContext,
                                parent_answer_pk=self.pk,
                            )
                            new_question.append(local_new_question)
                # print('NEW QUESTIONS', new_question)
                if len(new_question) > 0:
                    for question in new_question:
                        self.addQuestionToQueue(question)
            finally: 
                self._creating_related = False



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

class EmailMessage(models.Model):
    created = models.DateTimeField(_("Date created"), auto_now_add=True)
    subject = models.CharField(_("Header"), max_length=255)
    html_content = models.TextField(_("HTML-code"))
    users = models.ManyToManyField(User, verbose_name=_("Users"), blank=True)
    groups = models.ManyToManyField(Group, verbose_name=_("Groups"), blank=True)

    class Meta:
        verbose_name = _("Email mail")
        verbose_name_plural = _("Email messages")
        ordering = ['-created']

    def __str__(self):
        return self.subject


class Transaction(models.Model):
    created = models.DateTimeField(_("Date created"), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(_("Amount"), default=0)
    project = models.ForeignKey(Project, verbose_name=_("Project"), on_delete=models.CASCADE)
    
    
