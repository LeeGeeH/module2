# -*- coding: utf-8 -*-
import requests

data = {"destination": "10,0,20"}
response = requests.post("http://127.0.0.1:5050/set_destination", json=data)
print(response.text)