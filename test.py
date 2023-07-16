import json

import requests

try:
    with open("coin_list.json", "r") as file:
        data = json.load(file)
except FileNotFoundError:
    url = "https://api.coingecko.com/api/v3/coins/list"

    response = requests.get(url)

    print(response)
