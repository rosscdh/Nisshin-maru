import os
import time
import pprint
import requests

TOKEN = os.getenv('TOKEN', '')
INSTANA_ENDPOINT = os.getenv('INSTANA_ENDPOINT', '')
MAX_ERROR_RATE = float(os.getenv('MAX_ERROR_RATE', '1.5'))
REFRESH = int(os.getenv('REFRESH', 10))

assert TOKEN, 'You must define a TOKEN'
assert INSTANA_ENDPOINT, 'You must define a INSTANA_ENDPOINT'
#https://tmde2-vorwerkprod.instana.io/#/analyze;callList.dataSource=calls;callList.groupBy=%7B%22name%22%3A%22kubernetes.pod.name%22%7D;callList.tagFilter;groups.metrics=!(metric~latency~aggregation~MEAN)(metric~errors~aggregation~MEAN)~;groups.orderBy=errors_MEAN_Agg;groups.orderDirection=DESC?timeline.to&timeline.ws=300000&timeline.fm&timeline.ar=true

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
        #import pdb;pdb.set_trace()
        if error_rate >= MAX_ERROR_RATE:
            # pprint.pprint(data)
            # pprint.pprint(error_rate)
            info['message'] = '{} is erroring: error_rate: {}'.format(service, error_rate)
            info['cmd'] = 'oc delete pod {}'.format(service)
            print("\033[1;31;40m {}".format(info))
        else:
            info['message'] = '{} is ok: error_rate: {}'.format(service, error_rate)
            info['cmd'] = None
            print("\033[1;32;40m {}".format(info))
    

if __name__ == "__main__":
    while True:
        check_errors()
        time.sleep(REFRESH)