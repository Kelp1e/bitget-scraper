import json
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from cloudscraper import create_scraper
from requests import HTTPError

from db.models import ARB
from db.setup import create_session

scraper = create_scraper()


def request(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)

        response.raise_for_status()

        return response
    except HTTPError as error:
        if error.response.status_code == 429:
            # Logic with proxy here
            print(error)
            time.sleep(60)

            return request(func, *args, **kwargs)


def get_coin_list():
    try:
        with open("coin_list.json", "r") as file:
            data = json.load(file)

            return data
    except FileNotFoundError:
        url = "https://api.coingecko.com/api/v3/coins/list"

        response = request(scraper.get, url).json()

        with open("coin_list.json", "w") as file:
            json.dump(response, file)

        return response


def get_token_id_by_symbol(symbol, coin_list):
    for coin in coin_list:
        if coin.get("symbol") == symbol:
            return coin.get("id")


def get_spot_tokens(product_type):
    url = f"https://api.bitget.com/api/mix/v1/market/contracts?productType={product_type}"

    response = request(scraper.get, url).json()

    return response


# TOKEN_SYMBOL FIELD
def get_token_symbol(token):
    token_symbol = token.get("baseCoin").lower()

    return token_symbol


# ORDERS FIELD
def get_token_orders(token):
    symbol = token.get("symbol")

    url = f"https://api.bitget.com/api/mix/v1/market/depth?symbol={symbol}&limit=100"

    response = request(scraper.get, url)

    if response:
        return response.json().get("data")


# CONTRACTS FIELD
def get_token_contracts(token, coin_list):
    symbol = get_token_symbol(token)

    token_id = get_token_id_by_symbol(symbol, coin_list)

    url = f"https://api.coingecko.com/api/v3/coins/{token_id}"

    response = request(scraper.get, url)

    if not response:
        return

    data = response.json()
    detail_platforms = data.get("detail_platforms")

    contracts = {}

    # Ethereum contract
    ethereum = detail_platforms.get("ethereum")

    if ethereum:
        contracts["ethereum"] = ethereum.get("contract_address")

    # BSC contract
    bsc = detail_platforms.get("binance-smart-chain")

    if bsc:
        contracts["bsc"] = bsc.get("contract_address")

    return contracts


# CHANGE_5M FIELD
def get_token_change_price(contracts):
    if contracts:
        bsc = contracts.get("bsc")
        ethereum = contracts.get("ethereum")

        address = bsc if bsc else ethereum

        response = request(
            scraper.get, f"https://api.dexscreener.com/latest/dex/search?q={address}"
        ).json()

        pairs = response.get("pairs")

        if pairs:
            first_pair = pairs[0]
            price_change = first_pair.get("priceChange")
            change_5m = price_change.get("m5")

            return change_5m


def load_data(s, token, coin_list):
    token_symbol = get_token_symbol(token)
    print(token_symbol)
    token_orders = get_token_orders(token)
    token_contracts = get_token_contracts(token, coin_list)
    token_change_price = get_token_change_price(token_contracts)

    arb = s.query(ARB).filter_by(token_symbol=token_symbol).first()

    if arb:
        arb.orders = token_orders
        arb.change_5m = token_change_price
    else:
        arb = ARB(
            token_symbol=token_symbol,
            orders=token_orders,
            contracts=token_contracts,
            change_5m=token_change_price,
        )

    s.add(arb)
    s.commit()


def update_token_orders(tokens_data):
    session = create_session()
    s = session()

    for token in tokens_data:
        token_symbol = get_token_symbol(token)
        token_orders = get_token_orders(token)

        arb = s.query(ARB).filter_by(token_symbol=token_symbol).first()

        if arb:
            arb.orders = token_orders
        else:
            arb = ARB(token_symbol=token_symbol, orders=token_orders)

        s.add(arb)
        s.commit()

    s.close()


def update_token_change_price(coin_list, tokens_data):
    session = create_session()
    s = session()

    for token in tokens_data:
        token_contracts = get_token_contracts(token, coin_list)
        token_change_price = get_token_change_price(token_contracts)
        token_symbol = get_token_symbol(token)

        arb = s.query(ARB).filter_by(token_symbol=token_symbol).first()

        if arb:
            arb.change_5m = token_change_price
        else:
            arb = ARB(token_symbol=token_symbol, change_5m=token_change_price)

        s.add(arb)
        s.commit()

    s.close()


def main():
    session = create_session()
    s = session()

    coin_list = get_coin_list()

    tokens_data = get_spot_tokens("umcbl").get("data")

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_token_orders, args=(tokens_data,), trigger=IntervalTrigger(minutes=20))
    scheduler.add_job(update_token_change_price, args=(coin_list, tokens_data), trigger=IntervalTrigger(minutes=5))
    scheduler.start()

    # Load data
    try:
        for token in tokens_data:
            load_data(s, token, coin_list)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
