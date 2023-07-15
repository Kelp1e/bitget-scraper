import random
import time

import requests
from cloudscraper import create_scraper
from requests import HTTPError
from requests.auth import HTTPProxyAuth

from db.models import ARB
from db.setup import create_session
from proxies.proxies import get_proxies
from request_data.spot import json_data
from test import qkeys

scraper = create_scraper()


def request(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)

        response.raise_for_status()

        return response
    except HTTPError as error:
        if error.response.status_code == 429:
            # Logic with proxy here
            time.sleep(5)

            return func(*args, **kwargs)


def get_test(qkey, headers):
    response = request(scraper.get, f"https://api.arkhamintelligence.com/intelligence/search?query={qkey}",
                       headers=headers)

    return response


def get_spot_tokens():
    url = "https://www.bitget.com/v1/mix/market/homeQuotation"

    response = scraper.post(url, json=json_data).json()

    return response


def get_token_symbol(token):
    token_symbol = token.get("baseSymbol")

    return token_symbol


def get_token_exchange_code(token):
    exchange_code = token.get("exchangeCode")

    return exchange_code


def get_token_orders(token):
    symbol = token.get("symbolId")

    url = "https://api.bitget.com/api/spot/v1/market/depth?symbol={}"

    response = scraper.get(url.format(symbol)).json().get("data")

    return response


def get_token_contracts(token):
    pass


def get_token_change_price(token):
    pass


def load_data(s, tokens_data, proxies):
    for token in tokens_data[:10]:
        token_symbol = get_token_symbol(token)
        token_exchange_code = get_token_exchange_code(token)
        token_orders = get_token_orders(token)

        print(token_symbol, token_exchange_code, token_orders)

        arb = s.query(ARB).filter_by(exchange_code=token_exchange_code).first()

        if arb:
            arb.orders = token_orders
        else:
            arb = ARB(
                token_symbol=token_symbol,
                exchange_code=token_exchange_code,
                orders=token_orders,
            )

        s.add(arb)
        s.commit()


def main():
    # session = create_session()
    # s = session()
    #
    # proxies = get_proxies()
    #
    # tokens_data = get_spot_tokens().get("data")
    #
    # load_data(s, tokens_data, proxies)
    headers = {
        "authorization": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE0ZWI4YTNiNjgzN2Y2MTU4ZWViNjA3NmU2YThjNDI4YTVmNjJhN2IiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiS2VscDFlIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2Fya2hhbS1kZXYtMjgxNDIzIiwiYXVkIjoiYXJraGFtLWRldi0yODE0MjMiLCJhdXRoX3RpbWUiOjE2ODc2OTI0NzAsInVzZXJfaWQiOiJGZzJSUlY5cU9HVGNRc28zR01iYmZQclgxMnIxIiwic3ViIjoiRmcyUlJWOXFPR1RjUXNvM0dNYmJmUHJYMTJyMSIsImlhdCI6MTY4OTQwNDk1NiwiZXhwIjoxNjg5NDA4NTU2LCJlbWFpbCI6InZsYWRrbHAyMkBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsidmxhZGtscDIyQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.J9vUbnxk9BYq-PwhQI8FSr3brr5hZnua5nOmz4zkJwyLo_Hyfw8PJw0RYn3zaNZL9d3dN1AGoHFl0W_SFk4we0w68NrapZgev9mbynpDnppIwTRjaK0de6qWi573DFTk4LMogp8ks4eKnfw_AkSwqSR4TurvbLsnNYH2tQzt6r-dyCBTZMXY0LdYIm3P3483WfaEzE9xeKBeKpRoItZEvmQU0pkM0B__2SNTDGM9CYL2ref2TvJoPEPepku1qgmBVSbmaoHTkR3qjWSy4DqAHs1F5mhH1nuA_PAolBx1JXwYiTdd4SQbtIrHFPI5q80DV9nUuUnvxJpUwD2dN1cg-g"
    }

    while True:
        for i in qkeys:
            test = get_test(i, headers)
            print(test)


if __name__ == "__main__":
    main()
