from cloudpayments import CloudPayments
from cloudpayments.errors import CloudPaymentsError
from cloudpayments.models import Transaction
import decimal
import requests
from requests.auth import HTTPBasicAuth
import json
import os

params = {
            'Token': 'tk_ba86bc3759b5b04f3afc9ade0b547',
            'Amount': 9120,
            'AccountId': '+79771125519',
            'Currency': 'RUB',
                "Payer": { 
                "FirstName": 'Гулчехра',
                "LastName":  'Фаиль',
                "MiddleName": '-',
                "Address": 'Москва, ул. Генерала Антонова, д.3',
                "City":"MO",
                "Country":"RU",
                "Phone": '+79771125519',
            },

            "Escrow": {
                "AccumulationId": '5466982', 
                "TransactionIds": [int('2096583704')],
                "EscrowType": "OneToN",
                "FinalPayout": True
            }
}


def _send_topup_request(cp, endpoint, params=None, request_id=None):
    auth = HTTPBasicAuth('pk_f3458b2cceee2b656a28cb5fbd49c', 'd69ab4a9e872f527a818d8b0198b716f')
    headers = None
    
    with open('text.txt', 'w') as file:
        json.dump(params, file)

    os.system('openssl cms -sign -signer certificate.crt -inkey private.key -out sign.txt -in text.txt -outform pem')    

    f = open('sign.txt')
    lines = f.readlines()
    
    headers = {
        'X-Signature': ''.join(map(lambda x: x[:-1], lines[1:-1]))
    }



    if request_id is not None:
        headers['X-Request-ID'] = request_id
    
    response = requests.post(cp.URL + endpoint, json=params, auth=auth, headers=headers)
    print('SEND REQUEST', response.request.body,response.request.headers, response.request.hooks,)
    return response.json(parse_float=decimal.Decimal)


def topup(cp, params):
        print('PARAPMS', params)

        response = _send_topup_request(cp, 'payments/token/topup', params)
        print('RESPONSE TOPUP', response)


        if response['Success']:
           return Transaction.from_dict(response['Model'])
        raise CloudPaymentsError(response)

cp = CloudPayments('pk_f3458b2cceee2b656a28cb5fbd49c', 'd69ab4a9e872f527a818d8b0198b716f')

response = topup(cp, params)
print(response)
