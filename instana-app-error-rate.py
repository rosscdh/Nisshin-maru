import os
import time
import json
import pprint
import requests

import numpy as np
import pandas as pd

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

TOKEN = os.getenv('TOKEN', '')
INSTANA_ENDPOINT = os.getenv('INSTANA_ENDPOINT', '')
MAX_ERROR_RATE = float(os.getenv('MAX_ERROR_RATE', '1.5'))
REFRESH = int(os.getenv('REFRESH', 10))
SHOW_ONLY_ERRORS = int(os.getenv('SHOW_ONLY_ERRORS', 1))

assert TOKEN, 'You must define a TOKEN'
assert INSTANA_ENDPOINT, 'You must define a INSTANA_ENDPOINT'

TRENDS = dict()
PREVIOUS = dict()

Item = Query()

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

def check_errors(db):
    items = get_data()
    when = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    # print('*****' * 10)
    # print('********** {} **********'.format(when))
    # print('*****' * 10)
    #pprint.pprint(items)
    entries = []
    for data in items:

        metrics_a, error_rate = data.get('metrics', {}).get('errorsAgg', [])[0]
        service = data.get('name')

        info = {
            'service': service,
            'error_rate': error_rate,
            'message': '',
            'when': when,
            'trending': None,
            'trend': None,
        }

        qs = db.search(Item.service==service)[0:30]
        if qs:
            df = pd.DataFrame(qs)
            df.sort_values('when', inplace=True)

            info['trending'] = 'steady'
            info['trend'] = df.error_rate.mean()
            if df.error_rate.is_monotonic_increasing is True:
                info['trending'] = 'up'
            if df.error_rate.is_monotonic_decreasing is True:
                info['trending'] = 'down'
            if info['trend'] == 0.0:
                info['trending'] = '-'


        #if error_rate >= MAX_ERROR_RATE:
        if info['trending'] in ['up', 'down']:
            if info['trending'] in ['up']:
                info['message'] = '{} is trending up: error_rate: {}'.format(service, error_rate)
                info['cmd'] = 'oc delete pod {}'.format(service)
                print("\033[1;31;40m {}".format(json.dumps(info)))

            if info['trending'] in ['down']:
                info['message'] = '{} is trending down'.format(service)
                print("\033[1;32;40m {}".format(json.dumps(info)))
        else:
            if SHOW_ONLY_ERRORS == 0:
                info['message'] = '{} is ok'.format(service)
                info['cmd'] = None
                print("\033[1;248;40m {}".format(json.dumps(info)))

        entries.append(info)

    db.insert_multiple(entries)
    

if __name__ == "__main__":
    while True:
        db = TinyDB('db.json', storage=CachingMiddleware(JSONStorage))
        check_errors(db=db)
        # import pdb;pdb.set_trace()
        time.sleep(REFRESH)
        db.close()