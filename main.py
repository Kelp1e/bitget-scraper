import time

from cloudscraper import create_scraper
from requests import HTTPError

from db.models import ARB
from db.setup import create_session
from request_data.spot import json_data

scraper = create_scraper()


def request(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)

        response.raise_for_status()

        return response
    except HTTPError as error:
        if error.response.status_code == 429:
            # Logic with proxy here
            time.sleep(60)

            return request(func, *args, **kwargs)


def get_token_id_by_symbol(symbol, coin_list):
    for coin in coin_list:
        if coin.get("symbol") == symbol:
            return coin.get("id")


def get_spot_tokens():
    url = "https://www.bitget.com/v1/mix/market/homeQuotation"

    response = request(scraper.post, url, json=json_data).json()

    return response


# TOKEN_SYMBOL FIELD
def get_token_symbol(token):
    token_symbol = token.get("baseSymbol").lower()

    return token_symbol


# EXCHANGE_CODE FIELD
def get_token_exchange_code(token):
    exchange_code = token.get("exchangeCode").lower()

    return exchange_code


# ORDERS FIELD
def get_token_orders(token):
    symbol = token.get("symbolId")

    url = f"https://api.bitget.com/api/spot/v1/market/depth?symbol={symbol}"

    response = request(scraper.get, url).json().get("data")

    return response


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


def load_data(s, tokens_data, coin_list):
    for token in tokens_data:
        token_symbol = get_token_symbol(token)
        token_exchange_code = get_token_exchange_code(token)
        token_orders = get_token_orders(token)
        token_contracts = get_token_contracts(token, coin_list)
        token_change_price = get_token_change_price(token_contracts)

        arb = s.query(ARB).filter_by(exchange_code=token_exchange_code).first()

        if arb:
            arb.orders = token_orders
            arb.change_5m = token_change_price
        else:
            arb = ARB(
                token_symbol=token_symbol,
                exchange_code=token_exchange_code,
                orders=token_orders,
                contracts=token_contracts,
                change_5m=token_change_price
            )

        s.add(arb)
        s.commit()


def main():
    session = create_session()
    s = session()

    coin_list = request(
        scraper.get, "https://api.coingecko.com/api/v3/coins/list"
    ).json()

    tokens_data = get_spot_tokens().get("data")

    load_data(s, tokens_data, coin_list)


if __name__ == "__main__":
    main()
