import pytest
import http.client as httpc
import json
from datetime import date, datetime
import urllib.parse

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

def test_home_route():
    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("GET", "/")
    res = conn.getresponse()

    assert res.status == 200

def test_login_route():
    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("GET", "/login")
    res = conn.getresponse()

    assert res.status == 200

def test_register_route():
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_data = {"username": time_now, "password": time_now}
    data = urllib.parse.urlencode(form_data).encode('utf-8')
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": len(data)
    }

    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("POST", "/register", data, headers)
    res = conn.getresponse()

    # Check for successful redirect on account creation
    if res.status == 302:
        conn.request("POST", "/login", data, headers)
        res = conn.getresponse()

        # Check for redirect on successful login
        assert res.status == 302

def test_reports_route():
    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("GET", "/reports")
    res = conn.getresponse()

    assert res.status == 200

def test_report_pdf():
    today = date.today().strftime("%Y-%m-%d")
    form_data = {"start_date": today, "end_date": today}
    data = urllib.parse.urlencode(form_data).encode('utf-8')
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": len(data)
    }

    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("POST", "/reports", data, headers)
    res = conn.getresponse()

    assert res.status == 200

def test_admin_route():
    conn = httpc.HTTPConnection("localhost", 5000)
    conn.request("GET", "/admin")
    res = conn.getresponse()

    assert res.status == 302
