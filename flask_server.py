from flask import Flask, request
import requests
import json
import os

sms_api_key = os.environ['MTS_API_KEY']
crm_api_key = os.environ['CRM_API_KEY']
crm_phone = os.environ['CRM_ACCOUNT_PHONE']
mng_phone = os.environ['MANAGER_PHONE']

def take_phone_by_id(client_id):
    request_to_crm = {"request": {
    "client_id": client_id
      }
    }
    resp = requests.post('https://myfavouritecrm.envycrm.com/openapi/v1/client/getContacts/', 
        params={'api_key': crm_api_key}, json=request_to_crm)
    print((resp.text))
    if not resp.status_code == 200:
        print('Can''t take client phone from CRM')
        return None
    ans = json.loads(resp.text)['result']['contacts']
    for c in ans:
        if c['type_id'] == 1:
            return c['value']
    return None
    
    
def send_SMS(recepient: str, send_str: str):
    payload = {'number': crm_phone, 'destination': recepient, 'text': send_str}
    r = requests.post(r'https://api.exolve.ru/messaging/v1/SendSMS', headers={'Authorization': 'Bearer '+sms_api_key}, data=json.dumps(payload))
    print(r.text)
    return r.text, r.status_code

app = Flask(__name__)

@app.route('/send_SMS', methods=['POST'])
def receive_data():
    CRM_data = request.form.to_dict()
    
    client_name = CRM_data.get('lead[values][main][inputs][name][value]', None)
    client_phone = CRM_data.get('lead[values][main][inputs][phone][value]', None)
    client_id = CRM_data.get('deal[client_id]', None)
    
    
    enevt_type = CRM_data.get('event', None) or 'unknown event'
    recepient = mng_phone
    
    if enevt_type == 'create_lead' and client_name and client_phone:
        send_str = f'Заявка от клиента  {client_name}'
    elif enevt_type == 'create_deal' and client_id:
        send_str = 'Ваша заявка взята в работу'
        client_phone = take_phone_by_id(client_id)
        if not client_phone:
            send_str = 'Сообщение клиенту не отправлено'
        else:
            recepient = client_phone
    else:
        print('Неверный запрос')
        return 'Bad request', 400

    return send_SMS(recepient, send_str)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
