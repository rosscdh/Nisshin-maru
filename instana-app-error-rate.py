import os
import time
import json
import pprint
import requests
from alkali import Database, Model, fields, tznow

TOKEN = os.getenv('TOKEN', '')
INSTANA_ENDPOINT = os.getenv('INSTANA_ENDPOINT', '')
MAX_ERROR_RATE = float(os.getenv('MAX_ERROR_RATE', '1.5'))
REFRESH = int(os.getenv('REFRESH', 10))
SHOW_ONLY_ERRORS = int(os.getenv('SHOW_ONLY_ERRORS', 1))

assert TOKEN, 'You must define a TOKEN'
assert INSTANA_ENDPOINT, 'You must define a INSTANA_ENDPOINT'

TRENDS = dict()
PREVIOUS = dict()


{"service": "recipe-details-28-b75tp", "error_rate": 0.0, "message": "recipe-details-28-b75tp is ok", "when": "2019-03-11 15:43:50", "cmd": null}

class Entry(Model):
   when           = fields.DateTimeField(primary_key=True)
   service        = fields.StringField()
   message        = fields.StringField()
   cmd            = fields.StringField()
   error_rate     = fields.FloatField()
   created        = fields.DateTimeField(auto_now_add=True)

db = Database(models=[Entry], save_on_exit=True)


def get_data():
    headers = {
        'Authorization': 'apiToken {}'.format(TOKEN),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
   
    data = {
        "metrics": [
            {
                "metric": "errors",
                "aggregation": "MEAN"
            },
            {
                "metric": "latency",
                "aggregation": "MEAN"
            }
        ],
        "group": {
            "groupbyTag": "kubernetes.pod.name"
        },
        "pagination": {
            "retrievalSize": 100,
            "offset": 0,
            "ingestionTime": 0
        },
    }
    resp = requests.post(INSTANA_ENDPOINT,
                         json=data,
                         headers=headers)

    #import pdb;pdb.set_trace()
    if resp.ok:
        return resp.json().get('items', [])
    else:
        print(resp.status_code, resp.content)
        return []

def check_errors():
    items = get_data()
    when = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    # print('*****' * 10)
    # print('********** {} **********'.format(when))
    # print('*****' * 10)
    #pprint.pprint(items)
    for data in items:
        #import pdb;pdb.set_trace()
        metrics_a, error_rate = data.get('metrics', {}).get('errorsAgg', [])[0]
        service = data.get('name')

        info = {
            'service': service,
            'error_rate': error_rate,
            'message': '',
            'when': when
        }
        # PREVIOUS[service] = 0 if service not in PREVIOUS else PREVIOUS[service][0:10] 
        # TRENDS[service] = [] if service not in TRENDS else TRENDS[service][0:10]
        # TRENDS[service].insert(0, error_rate)

        # trend = sum(TRENDS[service])

        # if PREVIOUS[service] > trend:
        #     trending = 'up'
        # elif PREVIOUS[service] < trend:
        #     trending = 'down'
        # else:
        #     trending = 'no-change'

        # info['trending'] = trending
        # PREVIOUS[service] = trend
        
        if error_rate >= MAX_ERROR_RATE:
            info['message'] = '{} is erroring: error_rate: {}'.format(service, error_rate)
            info['cmd'] = 'oc delete pod {}'.format(service)
            print("\033[1;31;40m {}".format(json.dumps(info)))
        else:
            if SHOW_ONLY_ERRORS == 0:
                info['message'] = '{} is ok'.format(service)
                info['cmd'] = None
                print("\033[1;32;40m {}".format(json.dumps(info)))

        entry = Entry(**info)
        entry.save()

    db.store()
    

if __name__ == "__main__":
    while True:
        check_errors()
        time.sleep(REFRESH)