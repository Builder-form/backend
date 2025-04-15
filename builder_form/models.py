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

    def delete_question_recursive(self, question):
        """
        Рекурсивно удаляет вопрос и все его дочерние вопросы (детей, внуков и т.д.)
        Также удаляет ответы на эти вопросы и убирает их из очереди и истории
        """
        # Получить историю вопросов
        history = list(self.history_queue.split(','))
        self.normalize_history_or_queue(history)
        
        # Найти всех детей вопроса
        children = QuestionInstance.objects.filter(parent_pk=question.pk)
        
        # Рекурсивно удалить всех детей
        for child in children:
            self.delete_question_recursive(child)
        
        # Удалить ответы на вопрос
        AnswerQuestion.objects.filter(question_instance=question.pk, project=self).delete()
        
        # Удалить вопрос из очереди
        try:
            self.deleteFromQueue(str(question.pk))
        except:
            pass
        
        # Удалить вопрос из истории
        if str(question.pk) in history:
            history.remove(str(question.pk))
            self.history_queue = ','.join(history)
        
        # Удалить сам вопрос
        question.delete()

    def back(self):
        
        current_question = self.get_current_question()
        
        # Получить родительский вопрос
        if current_question.parent_pk == 0:
            return None  # Нет родительского вопроса для возврата
        
        parent_question = QuestionInstance.objects.get(pk=current_question.parent_pk)
        
        # Определяем, является ли родительский вопрос "братом" другого вопроса
        # Если да, то нам нужно найти "дедушку" (родителя родителя)
        grandfather_pk = parent_question.parent_pk
        if grandfather_pk != 0:
            siblings_of_parent = QuestionInstance.objects.filter(parent_pk=grandfather_pk).exclude(pk=parent_question.pk)
            has_sibling_parent = siblings_of_parent.exists()
        else:
            has_sibling_parent = False
        
        # Получить историю вопросов
        history = list(self.history_queue.split(','))
        self.normalize_history_or_queue(history)
        
        # Если родительский вопрос имеет "братьев", и мы находимся после группы братьев
        if has_sibling_parent:
            # Найти последний отвеченный вопрос в истории, который является самым последним из "дядей" текущего вопроса
            grandfather = QuestionInstance.objects.get(pk=grandfather_pk)
            
            # Рекурсивно удалить текущий вопрос и все его дочерние вопросы
            self.delete_question_recursive(current_question)
            
            # Рекурсивно удалить родительский вопрос и все его дочерние вопросы (кроме текущего, который уже удален)
            # Это также удалит "дядей" текущего вопроса
            self.delete_question_recursive(parent_question)
            
            # Вернуть "дедушку" в очередь вопросов
            self.questions_queue = str(grandfather.pk) + ',' + self.questions_queue
            
            self.save()
            
            return grandfather
        else:
            # Стандартная логика - возврат к родительскому вопросу
            
            # Найти всех братьев текущего вопроса (вопросы с тем же родителем)
            sibling_questions = QuestionInstance.objects.filter(parent_pk=current_question.parent_pk)
            
            # Рекурсивно удалить всех братьев и их дочерние вопросы
            for sibling in sibling_questions:
                self.delete_question_recursive(sibling)
            
            # Удалить ответы на родительский вопрос (который теперь станет текущим)
            AnswerQuestion.objects.filter(question_instance=parent_question.pk, project=self).delete()
            
            # Найти и удалить родительский вопрос из истории, если он там есть
            try:
                if str(parent_question.pk) in history:
                    history.remove(str(parent_question.pk))
            except:
                pass
            
            self.history_queue = ','.join(history)
            self.questions_queue = str(parent_question.pk) + ',' + self.questions_queue
            
            self.save()
            
            return parent_question

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

        # def get_answer_text(list_qid):
        #     return [Answer.objects.get(id=qid).text for qid in list_qid]
        
        def get_answers(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
          
            answers_text = []
            
            for a in ans:
                try:
                    q = QuestionInstance.objects.get(pk=a.question_instance)
                except:
                    return answers_text
                #ЗАИФАНО
                if qid == 'Q29' and q.pk == parent_pk:
                    answers_text.append(a.answer_text)
                    continue
                #ЗАИФАНО
                while q.parent_pk != parent_pk:
                    try:
                        q = QuestionInstance.objects.get(pk=q.parent_pk)
                    except:
                        break
                
                if q.parent_pk == parent_pk:
                    answers_text.append(a.answer_text)
            return answers_text
        
       
        def add_string_report(string, qid):
            nonlocal report
            if len(get_answers(qid)) == 0:
                return
            else:
                report += string

        # if len(get_answers('Q30')) == 0 and len(get_answers('Q31')) == 0 and len(get_answers('Q32')) == 0:
        #     return '' исправить

        print("Q29 ANSWERS", get_answers('Q29'))

        report += f"<strong>Target Room purposes</strong>: {', '.join(get_answers('Q320'))}  {', '.join(get_answers('Q29'))}<br/>"
        

        add_string_report("<strong>1) Strip out and demolition</strong>:<br/>", 'Q34')
        add_string_report("<strong>Room type specific:</strong><br/>", 'Q34')
        add_string_report(self.formatPairAnswers(get_answers('Q34'), get_answers('Q35')), 'Q34')
        add_string_report(self.formatPairAnswers(get_answers('Q36'), get_answers('Q37')), 'Q36')
        add_string_report(self.formatPairAnswers(get_answers('Q38'), get_answers('Q39')), 'Q38')
        add_string_report(self.formatPairAnswers(get_answers('Q40'), get_answers('Q41')), 'Q40')
        add_string_report(self.formatPairAnswers(get_answers('Q42'), get_answers('Q43')), 'Q42')
        add_string_report(self.formatPairAnswers(get_answers('Q44'), get_answers('Q45')), 'Q44')
        add_string_report("<strong>Ceilings:</strong> <br/>", 'Q46')
        add_string_report(self.formatAnswers(get_answers('Q46')), 'Q46')
        add_string_report("<strong>Walls:</strong><br/>", 'Q47')
        add_string_report(self.formatPairAnswers(get_answers('Q47'), get_answers('Q48')), 'Q47')
        add_string_report("<strong>Floors:</strong> <br/>", 'Q49')
        add_string_report(self.formatPairAnswers(get_answers('Q49'), get_answers('Q50')), 'Q49')

        add_string_report("2) Structure improvement: <br/>", 'Q52')
        add_string_report("<strong>Ceilings:</strong> <br/>", 'Q52')
        add_string_report(self.formatAnswers(get_answers('Q52')), 'Q52')
        add_string_report("<strong>Walls:</strong> <br/>", 'Q53')
        add_string_report(self.formatAnswers(get_answers('Q53')), 'Q53')
        add_string_report("<strong>Floors:</strong> <br/>", 'Q54')
        add_string_report(self.formatAnswers(get_answers('Q54')), 'Q54')

        add_string_report("3) Internal decoration and finishes: <br/>", 'Q56')
        add_string_report("<strong>Ceilings:</strong> <br/>", 'Q56')
        add_string_report(self.formatAnswers(get_answers('Q56')), 'Q56')
        add_string_report("<strong>Walls:</strong> <br/>", 'Q57')
        add_string_report(self.formatPairAnswers(get_answers('Q57'), get_answers('Q58')), 'Q57')
        add_string_report("<strong>Floors:</strong> <br/>", 'Q59')
        add_string_report(self.formatPairAnswers(get_answers('Q59'), get_answers('Q60')), 'Q59')

        add_string_report("4) Fitting and installing: <br/>", 'Q63')
        add_string_report("Windows: <br/>", 'Q63')
        add_string_report(self.formatPairAnswers(get_answers('Q63'), get_answers('Q64')), 'Q63')
        add_string_report("External doors: <br/>", 'Q641')
        add_string_report(self.formatPairAnswers(get_answers('Q641'), get_answers('Q642')), 'Q641')
        add_string_report("Internal doors: <br/>", 'Q65')
        add_string_report(self.formatPairAnswers(get_answers('Q65'), get_answers('Q66')), 'Q65')
        add_string_report("Inside room/hallway/landings: <br/>", 'Q67')
        add_string_report(self.formatPairAnswers(get_answers('Q67'), get_answers('Q68')), 'Q67')
        add_string_report('Electrics: <br/>', 'Q69')
        add_string_report(self.formatPairAnswers(get_answers('Q69'), get_answers('Q70')), 'Q69')

        if get_answer('Q70') != '' or get_answer('Q87') != '' or get_answer('Q93') != '':
            add_string_report('Room type specific: <br/>', 'Q1')
            add_string_report('Kitchen / Ulitity: <br/>', 'Q70')
            add_string_report(self.formatPairAnswers(get_answers('Q70'),  get_answers('Q71')), 'Q70')
            add_string_report(self.formatPairAnswers(get_answers('Q72'), get_answers('Q73')), 'Q72')
            add_string_report(self.formatPairAnswers(get_answers('Q74'), get_answers('Q75')), 'Q74')
            add_string_report(self.formatAnswers(get_answers('Q76')), 'Q76')
            add_string_report(self.formatPairAnswers(get_answers('Q77'), get_answers('Q78')), 'Q77')
            add_string_report(self.formatPairAnswers(get_answers('Q79'), get_answers('Q80')), 'Q79')
            add_string_report(self.formatPairAnswers(get_answers('Q81'), get_answers('Q82')), 'Q81')
            add_string_report(self.formatPairAnswers(get_answers('Q83'), get_answers('Q84')), 'Q83')
            add_string_report(self.formatPairAnswers(get_answers('Q85'), get_answers('Q86')), 'Q85')
            
            add_string_report('Storage / Attic: <br/>', 'Q87')
            add_string_report(self.formatPairAnswers(get_answers('Q87'), get_answers('Q88')), 'Q87')
            add_string_report(self.formatPairAnswers(get_answers('Q89'), get_answers('Q90')), 'Q89')
            add_string_report(self.formatPairAnswers(get_answers('Q91'), get_answers('Q92')), 'Q91')

            add_string_report('Bathroom/shower/toilet: <br/>', 'Q93')
            add_string_report(self.formatPairAnswers(get_answers('Q93'), get_answers('Q94')), 'Q93')
            add_string_report(self.formatPairAnswers(get_answers('Q95'), get_answers('Q96')), 'Q95')
            add_string_report(self.formatAnswers(get_answers('Q97')), 'Q97')
            add_string_report(self.formatPairAnswers(get_answers('Q98'), get_answers('Q99')), 'Q98')
            add_string_report(self.formatPairAnswers(get_answers('Q100'), get_answers('Q101')), 'Q100')
            add_string_report(self.formatPairAnswers(get_answers('Q102'), get_answers('Q103')), 'Q102')
            add_string_report(self.formatPairAnswers(get_answers('Q104'), get_answers('Q105')), 'Q104')  
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
        
        def add_string_report(string, qid):
            nonlocal report
            if get_answer(qid) == '':
                return
            else:
                report += string
                
        if answered('Q3_A1'):
            add_string_report("<strong>House refurbishment</strong>: - " + ", ".join(get_answers('Q5')), 'Q5')
            if answered('Q5_A3'):
                add_string_report(" <strong>Demolition Details</strong>: <br/>", 'Q6')
                add_string_report(self.formatPairAnswers(get_answers('Q6'),get_answers('Q7')), 'Q6')

        if answered('Q3_A2'):
            add_string_report(f"House extension: <br/> Extension type: {get_answer('Q11')}<br/> Roof type: {get_answer('Q12')}<br/> Extension Purposes: {', '.join(get_answers('Q13'))}<br/>", 'Q11')

        if answered('Q3_A3'):
            add_string_report(f"Loft Conversion: <br/> Conversion Type: {get_answer('Q14')}<br/> Conversion Purposes: {', '.join(get_answers('Q15'))}<br/>", 'Q14')

        if answered('Q3_A4'):
            add_string_report(f"Porch:<br/> Roof Type: {get_answer('Q16')}<br/>", 'Q16')

        if answered('Q3_A5'):
            add_string_report(f"Garage Conversion:<br/> Conversion type:<br/> {get_answer('Q17')} <br/>Roof type: {get_answer('Q18')} <br/> Conversion Purposes: {', '.join(get_answers('Q19'))}<br/>", 'Q17')

        if answered('Q3_A6'):
            add_string_report(f"Basement:<br/> Basement Purposes: {', '.join(get_answers('Q20'))}<br/>", 'Q20')

        if answered('Q3_A7'):
            add_string_report(f"Outbuilding: <br/> Type: {get_answer('Q21')} <br/> Roof type: {get_answer('Q22')} <br/> Outbuilding Purposes: {', '.join(get_answers('Q23'))}<br/>, 'Q21'")

        add_string_report("<br/>Internal Refurbishment detalisation:<br/> ", 'Q24')
        if answered('Q24_A2'):
            add_string_report("Not needed<br/>", 'Q24')
        elif answered('Q24_A1'):
            add_string_report("Number of Rooms to Refurbish on each Floor:<br/> ", 'Q26')
            add_string_report(self.formatPairAnswers(get_answers('Q26'),get_answers('Q27')), 'Q26')

        report += '<br/>'
        report += key_word

        add_string_report("<br/>External Refurbishment detalisation:<br/>", 'Q106')
        if answered('Q106_A2') in get_answers('Q106'):
            add_string_report("Not needed<br/>", 'Q106')
            
        elif answered('Q106_A1'):
            if answered('Q107_A1'):
                add_string_report("Exterior house surfaces:<br/> ", 'Q107')
                if answered('Q108_A1'):
                    add_string_report(f"Roof:<br/> Type: {get_answer('Q109')}<br/> Work:{get_answer('Q110')} <br/> Work details:{', '.join(get_answers('Q111'))} / {', '.join(get_answers('Q112'))}<br/>", 'Q109')
                if answered('Q108_A2'):
                    add_string_report(f"Front wall: Work: {get_answer('Q113')}<br/> Work details: {', '.join(get_answers('Q114'))} / {', '.join(get_answers('Q115'))}<br/>",'Q113')
                if answered('Q108_A3'):
                    add_string_report(f"Back wall:<br/> Work: {get_answer('Q116')} <br/> Work details: {', '.join(get_answers('Q117'))} / {', '.join(get_answers('Q118'))}<br/>", 'Q116')
                if answered('Q108_A4'):
                    add_string_report(f"Left hand side wall (facing the house) <br/>Work: {get_answer('Q119')} <br/>Work details: {', '.join(get_answers('Q120'))} / {', '.join(get_answers('Q121'))}<br/>", 'Q119')
                if answered('Q108_A5'):
                    add_string_report(f"Right hand side wall (facing the house) <br/>Work: {get_answer('Q122')} <br/>Work details: {', '.join(get_answers('Q123'))} / {', '.join(get_answers('Q124'))}<br/>", 'Q122')
                
                add_string_report("External Electrics:<br/> ", 'Q125')
                add_string_report(self.formatPairAnswers(get_answers('Q125'),get_answers('Q126')), 'Q125')
            
            if answered('Q107_A2'):
                add_string_report("Driveway:<br/> ", 'Q127')
                add_string_report(self.formatPairAnswers(get_answers('Q127'),get_answers('Q128')), 'Q127')
            if answered('Q107_A3'):
                add_string_report("Side passage:<br/> ", 'Q130')
                add_string_report(self.formatPairAnswers(get_answers('Q130'),get_answers('Q131')), 'Q130')
            if answered('Q107_A4'):
                add_string_report("Garden:<br/> ", 'Q133')
                add_string_report(self.formatPairAnswers(get_answers('Q133'),get_answers('Q134')), 'Q133')
                add_string_report(self.formatAnswers(get_answers('Q135')), 'Q135')
            if answered('Q107_A5'):
                add_string_report(f"<br/>{get_answer('Q107')}<br/>", 'Q107')
                
        return report

    @property
    def tree_for_builder(self):

        answers = AnswerQuestion.objects.all().filter(project=self)

        def answered(aid):
            nonlocal answers
            ans = answers.filter(answer__id=aid)
            return len(ans) > 0
        
        
        def get_answers(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            if len(ans) == 0:
                return ''
            return [answer.answer_text for answer in ans]
        
        def get_answer(qid):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            if len(ans) == 0:
                return ''
            return ans[0].answer_text

        def get_answers_with_context(qid, variables, prefixes):
            nonlocal answers
            ans = answers.filter(answer__question__id=qid)
            if len(ans) == 0:
                return ''
            return [answer.answer_text + ' - ' + ' - '.join([prefix + ': ' + QuestionInstance.objects.get(pk=answer.question_instance).context[var] for var, prefix in zip(variables, prefixes)]) for answer in ans]

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

        table['property_type']['text'] = ''.join(get_answers('Q2')) + ' ' + ''.join(get_answers('Q1'))

        if answered('Q1_A2'):
            table['project_type']['text'] += 'Flat refurbishment'
        else:
            table['project_type']['text'] += '<br/>'.join(get_answers('Q3'))

        report = ''

        def add_string_report(string, qid,):
            nonlocal report
            if get_answer(qid) == '':
                return
            report += string + '<br/>'
                

        if answered('Q1_A2'): #flat
            add_string_report("<strong>Project type detalisation</strong>: " + get_answer('Q4'), 'Q4')
            add_string_report("<strong>Refurbishment detalisation</strong>:", 'Q28')
            add_string_report("<strong>Number of Rooms to Refurbish</strong>:" + get_answer('Q28'), 'Q28')
            add_string_report('<br/>', 'Q34')
            
            add_string_report("1) Strip out and demolition: <br/>", 'Q34')
            add_string_report("Room type specific: <br/>", 'Q34')

            add_string_report(self.formatPairAnswers(get_answers('Q34'), get_answers_with_context('Q34', ['Room Sequence Number'], ['Room'])), 'Q34')
            add_string_report(self.formatPairAnswers(get_answers('Q36'), get_answers_with_context('Q37', ['Room Sequence Number'], ['Room'])), 'Q36')
            add_string_report(self.formatPairAnswers(get_answers('Q38'), get_answers_with_context('Q39', ['Room Sequence Number'], ['Room'])), 'Q38')
            add_string_report(self.formatPairAnswers(get_answers('Q40'), get_answers_with_context('Q41', ['Room Sequence Number'], ['Room'])), 'Q40')
            add_string_report(self.formatPairAnswers(get_answers('Q42'), get_answers_with_context('Q43', ['Room Sequence Number'], ['Room'])), 'Q42')
            add_string_report(self.formatPairAnswers(get_answers('Q44'), get_answers_with_context('Q45', ['Room Sequence Number'], ['Room'])), 'Q44')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q46')
            add_string_report(self.formatAnswers(get_answers_with_context('Q46', ['Room Sequence Number'], ['Room'])), 'Q46')
            add_string_report("<strong>Walls:</strong><br/>", 'Q47')
            add_string_report(self.formatPairAnswers(get_answers('Q47'), get_answers_with_context('Q48', ['Room Sequence Number'], ['Room'])), 'Q47')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q49')
            add_string_report(self.formatPairAnswers(get_answers('Q49'), get_answers_with_context('Q50', ['Room Sequence Number'], ['Room'])), 'Q49')

            add_string_report("2) Structure improvement: <br/>", 'Q52')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q52')
            add_string_report(self.formatAnswers(get_answers_with_context('Q52', ['Room Sequence Number'], ['Room'])), 'Q52')
            add_string_report("<strong>Walls:</strong> <br/>", 'Q53')
            add_string_report(self.formatAnswers(get_answers_with_context('Q53', ['Room Sequence Number'], ['Room'])), 'Q53')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q54')
            add_string_report(self.formatAnswers(get_answers_with_context('Q54', ['Room Sequence Number'], ['Room'])), 'Q54')

            add_string_report("3) Internal decoration and finishes: <br/>", 'Q56')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q56')
            add_string_report(self.formatAnswers(get_answers_with_context('Q56', ['Room Sequence Number'], ['Room'])), 'Q56')
            add_string_report("<strong>Walls:</strong> <br/>", 'Q57')
            add_string_report(self.formatPairAnswers(get_answers('Q57'), get_answers_with_context('Q58', ['Room Sequence Number'], ['Room'])), 'Q57')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q59')
            add_string_report(self.formatPairAnswers(get_answers('Q59'), get_answers_with_context('Q60', ['Room Sequence Number'], ['Room'])), 'Q59')

            add_string_report("4) Fitting and installing: <br/>", 'Q63')
            add_string_report("Windows: <br/>", 'Q63')
            add_string_report(self.formatPairAnswers(get_answers('Q63'), get_answers_with_context('Q64', ['Room Sequence Number'], ['Room'])), 'Q63')
            add_string_report("External doors: <br/>", 'Q641')
            add_string_report(self.formatPairAnswers(get_answers('Q641'), get_answers_with_context('Q642', ['Room Sequence Number'], ['Room'])), 'Q641')
            add_string_report("Internal doors: <br/>", 'Q65')
            add_string_report(self.formatPairAnswers(get_answers('Q65'), get_answers_with_context('Q66', ['Room Sequence Number'], ['Room'])), 'Q65')
            add_string_report("Inside room/hallway/landings: <br/>", 'Q67')
            add_string_report(self.formatPairAnswers(get_answers('Q67'), get_answers_with_context('Q68', ['Room Sequence Number'], ['Room'])), 'Q67')
            add_string_report('Electrics: <br/>', 'Q69')
            add_string_report(self.formatPairAnswers(get_answers('Q69'), get_answers_with_context('Q70', ['Room Sequence Number'], ['Room'])), 'Q69')

            if get_answer('Q70') != '' or get_answer('Q87') != '' or get_answer('Q93') != '':
                add_string_report('Room type specific: <br/>', 'Q1')
                add_string_report('Kitchen / Ulitity: <br/>', 'Q70')
                add_string_report(self.formatPairAnswers(get_answers('Q70'), get_answers_with_context('Q71', ['Room Sequence Number'], ['Room'])), 'Q70')
                add_string_report(self.formatPairAnswers(get_answers('Q72'), get_answers_with_context('Q73', ['Room Sequence Number'], ['Room'])), 'Q72')
                add_string_report(self.formatPairAnswers(get_answers('Q74'), get_answers_with_context('Q75', ['Room Sequence Number'], ['Room'])), 'Q74')
                add_string_report(self.formatAnswers(get_answers_with_context('Q76', ['Room Sequence Number'], ['Room'])), 'Q76')
                add_string_report(self.formatPairAnswers(get_answers('Q77'), get_answers_with_context('Q78', ['Room Sequence Number'], ['Room'])), 'Q77')
                add_string_report(self.formatPairAnswers(get_answers('Q79'), get_answers_with_context('Q80', ['Room Sequence Number'], ['Room'])), 'Q79')
                add_string_report(self.formatPairAnswers(get_answers('Q81'), get_answers_with_context('Q82', ['Room Sequence Number'], ['Room'])), 'Q81')
                add_string_report(self.formatPairAnswers(get_answers('Q83'), get_answers_with_context('Q84', ['Room Sequence Number'], ['Room'])), 'Q83')
                add_string_report(self.formatPairAnswers(get_answers('Q85'), get_answers_with_context('Q86', ['Room Sequence Number'], ['Room'])), 'Q85')
                
                add_string_report('Storage / Attic: <br/>', 'Q87')
                add_string_report(self.formatPairAnswers(get_answers('Q87'), get_answers_with_context('Q88', ['Room Sequence Number'], ['Room'])), 'Q87')
                add_string_report(self.formatPairAnswers(get_answers('Q89'), get_answers_with_context('Q90', ['Room Sequence Number'], ['Room'])), 'Q89')
                add_string_report(self.formatPairAnswers(get_answers('Q91'), get_answers_with_context('Q92', ['Room Sequence Number'], ['Room'])), 'Q91')

                add_string_report('Bathroom/shower/toilet: <br/>', 'Q93')
                add_string_report(self.formatPairAnswers(get_answers('Q93'), get_answers_with_context('Q94', ['Room Sequence Number'], ['Room'])), 'Q93')
                add_string_report(self.formatPairAnswers(get_answers('Q95'), get_answers_with_context('Q96', ['Room Sequence Number'], ['Room'])), 'Q95')
                add_string_report(self.formatAnswers(get_answers_with_context('Q97', ['Room Sequence Number'], ['Room'])), 'Q97')
                add_string_report(self.formatPairAnswers(get_answers('Q98'), get_answers_with_context('Q99', ['Room Sequence Number'], ['Room'])), 'Q98')
                add_string_report(self.formatPairAnswers(get_answers('Q100'), get_answers_with_context('Q101', ['Room Sequence Number'], ['Room'])), 'Q100')
                add_string_report(self.formatPairAnswers(get_answers('Q102'), get_answers_with_context('Q103', ['Room Sequence Number'], ['Room'])), 'Q102')
                add_string_report(self.formatPairAnswers(get_answers('Q104'), get_answers_with_context('Q105', ['Room Sequence Number'], ['Room'])), 'Q104')            
            
        if answered('Q1_A1'): #house
            add_string_report("<strong>Project type detalisation</strong>: " + get_answer('Q4'), 'Q4')
           
            add_string_report("<strong>House refurbishment:</strong>", 'Q5')
            add_string_report(self.formatAnswers(get_answers('Q5')), 'Q5')
            
            add_string_report("<strong>Demolition Details:</strong>", 'Q6')
            add_string_report(self.formatPairAnswers(get_answers('Q6'), get_answers('Q7')), 'Q6')

            if answered('Q3_A2'):
                add_string_report("<strong>House extention:</strong>", 'Q11')
                add_string_report("<strong>Extension type:</strong>" + get_answer('Q11'), 'Q11')
                add_string_report("<strong>Roof type:</strong>" + get_answer('Q12'), 'Q12')
                add_string_report("<strong>Extension Purposes:</strong>" + get_answer('Q13'), 'Q13')
            
            if answered('Q3_A3'):
                add_string_report("<strong>Loft conversion:</strong>", 'Q14')
                add_string_report("<strong>Conversion Type:</strong>" + get_answer('Q14'), 'Q14')
                add_string_report("<strong>Conversion Purposes:</strong>" + get_answer('Q15'), 'Q15')

            if answered('Q3_A4'):
                add_string_report("<strong>Porch:</strong>", 'Q16')
                add_string_report("<strong>Roof Type:</strong>" + get_answer('Q16'), 'Q16')

            if answered('Q3_A5'):
                add_string_report("<strong>Garage Conversion:</strong>", 'Q17')
                add_string_report("<strong>Conversion Type:</strong>" + get_answer('Q17'), 'Q17')
                add_string_report("<strong>Roof Type:</strong>" + get_answer('Q18'), 'Q18')
                add_string_report("<strong>Conversion Purposes:</strong>" + get_answer('Q19'), 'Q19')

            if answered('Q3_A6'):
                add_string_report("<strong>Basement:</strong>", 'Q20')
                add_string_report("<strong>Basement Purposes:</strong>" + get_answer('Q20'), 'Q20')

            if answered('Q3_A7'):
                add_string_report("<strong>Outbuilding:</strong>", 'Q21')
                add_string_report("<strong>Type:</strong>" + get_answer('Q21'), 'Q21')
                add_string_report("<strong>Roof Type:</strong>" + get_answer('Q22'), 'Q22')
                add_string_report("<strong>Outbuilding Purposes:</strong>" + get_answer('Q23'), 'Q23')            
            
            add_string_report("<strong>Internal Refurbishment detalisation:</strong>", 'Q24')

            if answered("Q24_A2"):
                add_string_report('Not needed', 'Q24')
            else:
                add_string_report('Number of Rooms to Refurbish on each FLoor: ', 'Q26')
                add_string_report(self.formatPairAnswers(get_answers('Q26'), get_answers('Q27')), 'Q26')
            
            # комнаты
            add_string_report("1) Strip out and demolition: <br/>", 'Q34')
            add_string_report("Room type specific: <br/>", 'Q34')

            add_string_report(self.formatPairAnswers(get_answers('Q34'), get_answers_with_context('Q34', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q34')
            add_string_report(self.formatPairAnswers(get_answers('Q36'), get_answers_with_context('Q37', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q36')
            add_string_report(self.formatPairAnswers(get_answers('Q38'), get_answers_with_context('Q39', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q38')
            add_string_report(self.formatPairAnswers(get_answers('Q40'), get_answers_with_context('Q41', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q40')
            add_string_report(self.formatPairAnswers(get_answers('Q42'), get_answers_with_context('Q43', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q42')
            add_string_report(self.formatPairAnswers(get_answers('Q44'), get_answers_with_context('Q45', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q44')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q46')
            add_string_report(self.formatAnswers(get_answers_with_context('Q46', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q46')
            add_string_report("<strong>Walls:</strong><br/>", 'Q47')
            add_string_report(self.formatPairAnswers(get_answers('Q47'), get_answers_with_context('Q48', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q47')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q49')
            add_string_report(self.formatPairAnswers(get_answers('Q49'), get_answers_with_context('Q50', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q49')

            add_string_report("2) Structure improvement: <br/>", 'Q52')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q52')
            add_string_report(self.formatAnswers(get_answers_with_context('Q52', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q52')
            add_string_report("<strong>Walls:</strong> <br/>", 'Q53')
            add_string_report(self.formatAnswers(get_answers_with_context('Q53', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q53')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q54')
            add_string_report(self.formatAnswers(get_answers_with_context('Q54', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q54')

            add_string_report("3) Internal decoration and finishes: <br/>", 'Q56')
            add_string_report("<strong>Ceilings:</strong> <br/>", 'Q56')
            add_string_report(self.formatAnswers(get_answers_with_context('Q56', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q56')
            add_string_report("<strong>Walls:</strong> <br/>", 'Q57')
            add_string_report(self.formatPairAnswers(get_answers('Q57'), get_answers_with_context('Q58', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q57')
            add_string_report("<strong>Floors:</strong> <br/>", 'Q59')
            add_string_report(self.formatPairAnswers(get_answers('Q59'), get_answers_with_context('Q60', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q59')

            add_string_report("4) Fitting and installing: <br/>", 'Q63')
            add_string_report("Windows: <br/>", 'Q63')
            add_string_report(self.formatPairAnswers(get_answers('Q63'), get_answers_with_context('Q64', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q63')
            add_string_report("External doors: <br/>", 'Q641')
            add_string_report(self.formatPairAnswers(get_answers('Q641'), get_answers_with_context('Q642', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q641')
            add_string_report("Internal doors: <br/>", 'Q65')
            add_string_report(self.formatPairAnswers(get_answers('Q65'), get_answers_with_context('Q66', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q65')
            add_string_report("Inside room/hallway/landings: <br/>", 'Q67')
            add_string_report(self.formatPairAnswers(get_answers('Q67'), get_answers_with_context('Q68', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q67')
            add_string_report('Electrics: <br/>', 'Q69')
            add_string_report(self.formatPairAnswers(get_answers('Q69'), get_answers_with_context('Q70', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q69')

            if get_answer('Q70') != '' or get_answer('Q87') != '' or get_answer('Q93') != '':
                add_string_report('Room type specific: <br/>', 'Q1')
                add_string_report('Kitchen / Ulitity: <br/>', 'Q70')
                add_string_report(self.formatPairAnswers(get_answers('Q70'), get_answers_with_context('Q71', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q70')
                add_string_report(self.formatPairAnswers(get_answers('Q72'), get_answers_with_context('Q73', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q72')
                add_string_report(self.formatPairAnswers(get_answers('Q74'), get_answers_with_context('Q75', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q74')
                add_string_report(self.formatAnswers(get_answers_with_context('Q76', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q76')
                add_string_report(self.formatPairAnswers(get_answers('Q77'), get_answers_with_context('Q78', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q77')
                add_string_report(self.formatPairAnswers(get_answers('Q79'), get_answers_with_context('Q80', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q79')
                add_string_report(self.formatPairAnswers(get_answers('Q81'), get_answers_with_context('Q82', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q81')
                add_string_report(self.formatPairAnswers(get_answers('Q83'), get_answers_with_context('Q84', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q83')
                add_string_report(self.formatPairAnswers(get_answers('Q85'), get_answers_with_context('Q86', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q85')
                
                add_string_report('Storage / Attic: <br/>', 'Q87')
                add_string_report(self.formatPairAnswers(get_answers('Q87'), get_answers_with_context('Q88', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q87')
                add_string_report(self.formatPairAnswers(get_answers('Q89'), get_answers_with_context('Q90', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q89')
                add_string_report(self.formatPairAnswers(get_answers('Q91'), get_answers_with_context('Q92', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q91')

                add_string_report('Bathroom/shower/toilet: <br/>', 'Q93')
                add_string_report(self.formatPairAnswers(get_answers('Q93'), get_answers_with_context('Q94', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q93')
                add_string_report(self.formatPairAnswers(get_answers('Q95'), get_answers_with_context('Q96', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q95')
                add_string_report(self.formatAnswers(get_answers_with_context('Q97', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q97')
                add_string_report(self.formatPairAnswers(get_answers('Q98'), get_answers_with_context('Q99', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q98')
                add_string_report(self.formatPairAnswers(get_answers('Q100'), get_answers_with_context('Q101', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q100')
                add_string_report(self.formatPairAnswers(get_answers('Q102'), get_answers_with_context('Q103', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q102')
                add_string_report(self.formatPairAnswers(get_answers('Q104'), get_answers_with_context('Q105', ['Room Sequence Number', 'Floor Name'], ['Room', 'Floor'])), 'Q104')            
            

            add_string_report("<strong>External Refurbishment detalisation:</strong>", 'Q106')

            if answered('Q106_A2'):
                add_string_report('Not needed', 'Q106')
            else:
                if answered("Q107_A1"):
                    add_string_report('Exterior house surfaces', "Q108")
                    if answered("Q108_A1"):
                        add_string_report("Roof: <br/>", 'Q109')
                        add_string_report("Type:" + self.formatAnswers(get_answers('Q109')), 'Q109')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q110')), 'Q110')
                    if answered("Q108_A2"):
                        add_string_report("Front wall: <br/>", 'Q113')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q113')), 'Q113')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q114'), get_answers('Q115')), 'Q114')
                    if answered("Q108_A3"):
                        add_string_report("Back wall: <br/>", 'Q116')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q116')), 'Q116')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q117'), get_answers('Q118')), 'Q117')
                    if answered("Q108_A4"):
                        add_string_report("Left hand side wall (facing the house): <br/>", 'Q119')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q119')), 'Q119')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q120'), get_answers('Q121')), 'Q120')
                    if answered("Q108_A5"):
                        add_string_report("Right hand side wall (facing the house): <br/>", 'Q122')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q122')), 'Q122')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q123'), get_answers('Q124')), 'Q123')
                    if answered("Q108_A6"):
                        add_string_report("External Electrics: <br/>", 'Q125')
                        add_string_report(self.formatPairAnswers(get_answers('Q125'), get_answers('Q126')), 'Q125')

                if (answered("Q107_A2")):
                    add_string_report("Driveway", 'Q128')
                    add_string_report(self.formatPairAnswers(get_answers('Q128'), get_answers('Q129')), 'Q128')

                if (answered("Q107_A3")):
                    add_string_report("Side passage", 'Q131')
                    add_string_report(self.formatPairAnswers(get_answers('Q131'), get_answers('Q132')), 'Q131')
                
                if (answered("Q107_A4")):
                    add_string_report("Garden", 'Q134')
                    add_string_report(self.formatPairAnswers(get_answers('Q134'), get_answers('Q135')), 'Q134')

                if (answered("Q107_A5")):
                    add_string_report(self.formatAnswers(get_answers('Q107')), 'Q107')

        table['list_of_work']['text'] = report
        return table

    @property
    def tree(self):
        answers = AnswerQuestion.objects.filter(project=self)

        def get_answers_pk(question_instance_pk):
            answers = AnswerQuestion.objects.filter(question_instance=question_instance_pk, project=self)
            return [answer.answer_text for answer in answers]
        
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

        def add_string_report(string, qid):
            nonlocal report
            if len(get_answers(qid)) == 0:
                return
            report += string + '<br/>'   
        

        table['property_type']['text'] = ''.join(get_answers('Q2')) + ' ' + ''.join(get_answers('Q1'))

        if answered('Q1_A2'):
            table['project_type']['text'] += 'Flat refurbishment'
        else:
            table['project_type']['text'] += '<br/>'.join(get_answers('Q3'))

        report = ''

        if answered('Q1_A2'): #flat
            add_string_report("<strong>Project type detalisation</strong>: " + get_answer('Q4'), 'Q4')
            add_string_report("<strong>Refurbishment detalisation</strong>:", 'Q28')
            add_string_report("<strong>Number of Rooms to Refurbish</strong>: " + get_answer('Q28'), 'Q28')
            add_string_report('<br/>', 'Q34')

            unique_rooms = set()
            for room in answers.filter(answer__question__id='Q29'):
                if room.question_instance not in unique_rooms:
                    unique_rooms.add(room.question_instance)
                    add_string_report("Room № " + QuestionInstance.objects.get(pk=room.question_instance).context["Room Sequence Number"], 'Q28')
                    report += self.generate_room_report(room.question_instance)
              
        if answered('Q1_A1'): #house
            add_string_report("<strong>Project type detalisation</strong>: " + get_answer('Q4'), 'Q4')
           
            add_string_report("<strong>House refurbishment:</strong>", 'Q5')
            add_string_report(self.formatAnswers(get_answers('Q5')), 'Q5')
            
            add_string_report("<strong>Demolition Details:</strong>", 'Q6')
            add_string_report(self.formatPairAnswers(get_answers('Q6'), get_answers('Q7')), 'Q6')

            if answered('Q3_A2'):
                add_string_report("<strong>House extention:</strong>", 'Q11')
                add_string_report("<strong>Extension type:</strong> " + get_answer('Q11'), 'Q11')
                add_string_report("<strong>Roof type:</strong>" + get_answer('Q12'), 'Q12')
                add_string_report("<strong>Extension Purposes:</strong> " + get_answer('Q13'), 'Q13')
            
            if answered('Q3_A3'):
                add_string_report("<strong>Loft conversion:</strong>", 'Q14')
                add_string_report("<strong>Conversion Type:</strong> " + get_answer('Q14'), 'Q14')
                add_string_report("<strong>Conversion Purposes:</strong> " + get_answer('Q15'), 'Q15')

            if answered('Q3_A4'):
                add_string_report("<strong>Porch:</strong>", 'Q16')
                add_string_report("<strong>Roof Type:</strong>" + get_answer('Q16'), 'Q16')

            if answered('Q3_A5'):
                add_string_report("<strong>Garage Conversion:</strong>", 'Q17')
                add_string_report("<strong>Conversion Type:</strong> " + get_answer('Q17'), 'Q17')
                add_string_report("<strong>Roof Type:</strong> " + get_answer('Q18'), 'Q18')
                add_string_report("<strong>Conversion Purposes:</strong> " + get_answer('Q19'), 'Q19')

            if answered('Q3_A6'):
                add_string_report("<strong>Basement:</strong>", 'Q20')
                add_string_report("<strong>Basement Purposes:</strong> " + get_answer('Q20'), 'Q20')

            if answered('Q3_A7'):
                add_string_report("<strong>Outbuilding:</strong>", 'Q21')
                add_string_report("<strong>Type:</strong> " + get_answer('Q21'), 'Q21')
                add_string_report("<strong>Roof Type:</strong> " + get_answer('Q22'), 'Q22')
                add_string_report("<strong>Outbuilding Purposes:</strong> " + get_answer('Q23'), 'Q23')            
            
            add_string_report("<strong>Internal Refurbishment detalisation:</strong>", 'Q24')

            if answered("Q24_A2"):
                add_string_report('Not needed', 'Q24')
            else:
                add_string_report('Number of Rooms to Refurbish on each FLoor: ', 'Q26')
                add_string_report(self.formatPairAnswers(get_answers('Q26'), get_answers('Q27')), 'Q26')
            

            # комнаты
            for room in answers.filter(answer__question__id='Q300'):
                ctx = QuestionInstance.objects.get(pk=room.question_instance).context
                add_string_report(ctx["Floor Name"] + " - Room № " + ctx["Room Sequence Number"], 'Q27')
                report += self.generate_room_report(room.question_instance)
            
            add_string_report("<strong>External Refurbishment detalisation:</strong>", 'Q106')

            if answered('Q106_A2'):
                add_string_report('Not needed', 'Q106')
            else:
                if answered("Q107_A1"):
                    add_string_report('Exterior house surfaces', "Q108")
                    if answered("Q108_A1"):
                        add_string_report("Roof: <br/>", 'Q109')
                        add_string_report("Type: " + self.formatAnswers(get_answers('Q109')), 'Q109')
                        add_string_report("Work: " + self.formatAnswers(get_answers('Q110')), 'Q110')
                    if answered("Q108_A2"):
                        add_string_report("Front wall: <br/>", 'Q113')
                        add_string_report("Work: " + self.formatAnswers(get_answers('Q113')), 'Q113')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q114'), get_answers('Q115')), 'Q114')
                    if answered("Q108_A3"):
                        add_string_report("Back wall: <br/>", 'Q116')
                        add_string_report("Work:" + self.formatAnswers(get_answers('Q116')), 'Q116')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q117'), get_answers('Q118')), 'Q117')
                    if answered("Q108_A4"):
                        add_string_report("Left hand side wall (facing the house): <br/>", 'Q119')
                        add_string_report("Work: " + self.formatAnswers(get_answers('Q119')), 'Q119')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q120'), get_answers('Q121')), 'Q120')
                    if answered("Q108_A5"):
                        add_string_report("Right hand side wall (facing the house): <br/>", 'Q122')
                        add_string_report("Work: " + self.formatAnswers(get_answers('Q122')), 'Q122')
                        add_string_report("Work details: <br/>" + self.formatPairAnswers(get_answers('Q123'), get_answers('Q124')), 'Q123')
                    if answered("Q108_A6"):
                        add_string_report("External Electrics: <br/>", 'Q125')
                        add_string_report(self.formatPairAnswers(get_answers('Q125'), get_answers('Q126')), 'Q125')

                if (answered("Q107_A2")):
                    add_string_report("Driveway", 'Q128')
                    add_string_report(self.formatPairAnswers(get_answers('Q128'), get_answers('Q129')), 'Q128')

                if (answered("Q107_A3")):
                    add_string_report("Side passage", 'Q131')
                    add_string_report(self.formatPairAnswers(get_answers('Q131'), get_answers('Q132')), 'Q131')
                
                if (answered("Q107_A4")):
                    add_string_report("Garden", 'Q134')
                    add_string_report(self.formatPairAnswers(get_answers('Q134'), get_answers('Q135')), 'Q134')

                if (answered("Q107_A5")):
                    add_string_report(self.formatAnswers(get_answers('Q107')), 'Q107')
        table['list_of_work']['text'] = report
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
                print("NEXT_ID", self.question_instance, next_id)
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
    
    
