# Query Instana for errors

Script to query Instana to get errors above a threshhold

```sh
SHOW_ONLY_ERRORS=1 TOKEN=qwerty123 INSTANA_ENDPOINT=https://YOURAPP.instana.io/api/application-monitoring/analyze/call-groups  python instana-app-error-rate.py
```

outputs

```sh
 {"service": "funky-application-18-f8bff", "error_rate": 0.0, "message": "funky-application-18-f8bff is ok: error_rate: 0.0", "when": "2019-03-11 14:03:30", "cmd": null}
 {"service": "funky-application-18-fjc5b", "error_rate": 0.0, "message": "funky-application-18-fjc5b is ok: error_rate: 0.0", "when": "2019-03-11 14:03:30", "cmd": null}
```

and when there are errors

```sh
{  
    "service":"funky-application-18-f8bff",
    "error_rate":0.0,
    "message":"funky-application-18-f8bff is ok: error_rate: 0.0",
    "when":"2019-03-11 14:03:30",
    "cmd":"oc delete pod funky-application-18-f8bff"
}
```

so now you can

```sh
oc delete pod funky-application-18-f8bff
```

or something

### notes

```
# will show ok messages too
SHOW_ONLY_ERRORS = 0
```