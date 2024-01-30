import requests
from django.conf import settings
from fast_bitrix24 import Bitrix
import json
from .models import ErrorLogs
from user.models import User

bx24 = Bitrix(getattr(settings, 'BITRIX_URL'))

def bitrix_add_lead(lead):
    answer = bx24.call('crm.lead.add',
        {
            "fields":{
                "TITLE": "Заявка с сайта id=" + str(lead.id),
                "NAME": lead.user.first_name,
                "LAST_NAME": lead.user.last_name,
                "STATUS_ID": "NEW",
                "STATUS_SEMANTIC_ID":"P",
                "PHONE": [ { "VALUE": lead.user.username, "VALUE_TYPE": "WORK" } ],
                "UF_CRM_KAKSVAMISVYAZ": lead.contact_type,
                "UF_CRM_KOGDASIDELKAD":lead.time_start,
                "UF_CRM_NAKAKOEVREMYA": lead.care_type,
                   
            },
            "params": { "REGISTER_SONET_EVENT": "Y" }
        }
    
    )
    return answer

def bitrix_delete_lead(id,  user='admin'):
    answer = '' 
    try:
            answer = bx24.call('crm.lead.delete',
            {
                "id": id
            }
            )
    except:
            ErrorLogs.objects.create(
               log=f'Не удалось удалить заказ, id: {id}',
                 user=User.objects.get(username=user) if type(user) == str else user
            )
    return answer
    
def bitrix_change_processed(id, cost, user='admin'):
    answer = ''
    try:
        answer =  bx24.call("crm.lead.update", 
        { 
            "id": id,
            "fields":
            { 
                "STATUS_DESCRIPTION":'Подобрано',
                "STATUS_ID": "UC_OMWAJG", 
                "STATUS_SEMANTIC_ID":"P",
                "CURRENCY_ID": "RUB", 
                "OPPORTUNITY": cost	
            },
            "params": { "REGISTER_SONET_EVENT": "Y", }		
        }
        )
    except:
        ErrorLogs.objects.create(
            log=f'Не удалось переместить заказ, id: {id}',
            user=User.objects.get(username=user) if type(user) == str else user
        )
    # answer = bx24.call("crm.lead.get", {'id':id})

    return answer

def bitrix_change_active(id,  user='admin'):
    answer = ''
    try:
        answer =  bx24.call("crm.lead.update", 
        { 
            "id": id,
            "fields":
            { 
                "STATUS_DESCRIPTION":'Активно',
                "STATUS_ID": "UC_UNEHBA", 
            },
            "params": { "REGISTER_SONET_EVENT": "Y", }		
        }
        )
    except:
        ErrorLogs.objects.create(
            log=f'Не удалось переместить заказ, id: {id}',
            user=User.objects.get(username=user) if type(user) == str else user
        )

    return answer


def bitrix_change_archive(id,  user='admin'):
    answer = ''
    try:
        answer =  bx24.call("crm.lead.update", 
        { 
            "id": id,
            "fields":
            { 
                "STATUS_DESCRIPTION":'В архиве',
                "STATUS_ID": "UC_0RIO8T", 
            },
            "params": { "REGISTER_SONET_EVENT": "Y", }		
        }
        )
    except:
        ErrorLogs.objects.create(
            log=f'Не удалось переместить заказ, id: {id}',
            user=User.objects.get(username=user) if type(user) == str else user
        )
        

    return answer