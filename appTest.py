import pytest
import http.client as httpc
import json

def test_realtime_metrics():
    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("GET", "/api/metrics/realtime", headers={ 'Accept': 'text/event-stream' })
    res = conn.getresponse()

    assert res.status == 200
    event = res.readline().decode('utf-8').strip()
    data = json.loads(event.replace('data: ', ''))

    for key in data['cpu']:
        assert data['cpu'][key] is not None

    for key in data['memory']:
        assert data['memory'][key] is not None

    assert len(data['disk']) > 0
    assert len(data['process']) > 0
