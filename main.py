#!/usr/bin/env python3

import json
import requests
import yfinance as yf
import time
import hmac
import hashlib
from urllib.parse import urlencode

from datetime import datetime, timedelta
from notion.collection import NotionDate
from config import settings
from notion.client import NotionClient
from prettytable import PrettyTable
# from urllib.request import urlopen

client = NotionClient(token_v2=settings.token)
yesterday_date = datetime.now() - timedelta(1)


def refresh_crypto():
    """Refresh Crypto table."""

    # Get table from Crypto page
    tbl = client.get_collection_view(settings.tables.crypto)

    # Get table data
    table_rows = tbl.collection.get_rows()
    # print(f'table_rows: {table_rows}')

    # Pretty table settings
    x = PrettyTable()
    x.field_names = ["Symbol", "Crypto Price", "Amount", "USD", "CZK"]
    # Column Alignment
    x.align["Symbol"] = "l"
    x.align["Crypto Price"] = "r"
    x.align["Amount"] = "r"
    x.align["USD"] = "r"
    x.align["CZK"] = "r"

    bitfinex_data = None

    # Iterate over notion table rows
    for row in table_rows:

        # Ignore empty rows if any
        if row.symbol == "":
            continue

        if "nanopool" in row.exchange.lower():
            amount = get_nanopool_amount(wallet=settings.wallets.nanopool.eth)
            print(f"FOUND nanopool: {row.symbol}: {amount}")
            row.amount = round(amount, 10)

        if "coinmate" in row.exchange.lower():
            amount = get_coinmate_amount()
            print(f"FOUND coinmate: {row.symbol}: {amount}")
            row.amount = amount

        if "bitfinex" in row.exchange.lower():
            if not bitfinex_data:
                bitfinex_data = get_bitfinex_data()

            found_value = [val[2] for val in bitfinex_data if val[1] == row.symbol]
            if not found_value:
                amount = 0
            else:
                amount = found_value[0]

            print(f"FOUND bitfinex: {row.symbol}: {amount}")
            row.amount = amount

    print(x)


def get_nanopool_amount(wallet):
    """Return amount of ETH in nanopool wallet.

    Docs: https://eth.nanopool.org/api
    """
    nanopool_url = f"https://api.nanopool.org/v1/eth/balance/{wallet}"
    content = requests.get(nanopool_url)
    data = content.json()
    amount = data['data']
    return amount


def get_coinmate_amount():
    """Return amount of BTC from coinmate."""

    def createSignature(clientId, apiKey, privateKey, nonce):
        message = str(nonce) + str(clientId) + apiKey
        signature = hmac.new(bytes(privateKey, 'latin-1'), bytes(message, 'latin-1'), digestmod=hashlib.sha256).hexdigest()
        return signature.upper()

    clientId = settings.api.coinmate.client_id
    public_key = settings.api.coinmate.public_key
    private_key = settings.api.coinmate.private_key
    nonce = int(time.time())
    signature = createSignature(clientId, public_key, private_key, nonce)

    url = "https://coinmate.io/api/balances"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    values = urlencode({'clientId': clientId, 'publicKey': public_key, 'nonce': nonce, 'signature': signature})
    content = requests.post(url, data=values, headers=headers)
    data = content.json()
    balance = data['data']['BTC']['balance']
    return balance


def get_bitfinex_data():
    """Return list-like data.
    [
        ['exchange', 'USD', 64.040459323497, 0, 64.040459323497, 'Exchange 300.0 DOGE for USD @ 0.65',
            {'reason': 'TRADE',
             'order_id': 64446937831,
             'order_id_oppo': 64455870683,
             'trade_price': '0.65',
             'trade_amount': '300.0'}
        ],
        ['exchange', 'ETH', 0.1, 0, 0.1, 'Exchange 0.00465863 ETH for USD @ 3487.9',
            {'reason': 'TRADE',
             'order_id': 64385422483,
             'order_id_oppo': 64384092659,
             'trade_price': '3487.9',
             'trade_amount': '-0.00465863'}
        ], ...
    """
    apiPath = 'v2/auth/r/wallets'
    url = f"https://api.bitfinex.com/{apiPath}"
    apiKey = settings.api.bitfinex.api_key
    apiSecret = settings.api.bitfinex.api_key_secret
    nonce = str(int(round(time.time() * 1000000)))
    body = ""
    signature = f"/api/{apiPath}{nonce}{body}"
    h = hmac.new(apiSecret.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
    sig = h.hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'bfx-nonce': nonce,
        'bfx-apiKey': apiKey,
        'bfx-signature': sig
    }

    content = requests.post(url, data={}, headers=headers)
    data = content.json()
    # print(f'data: {data}')
    return data


def get_coinbase_data():  # NOT WORKING
    """
    curl https://api.coinbase.com/v2/accounts \
        -H 'Authorization: Bearer abd90df5f27a7b170cd775abf89d632b350b7c1c9d53e08b340cd9832ce52c2c'

    API key is recommend if you only need to access your own account. All API key requests must be signed and contain the following headers:

    CB-ACCESS-KEY The api key as a string
    CB-ACCESS-SIGN The user generated message signature (see below)
    CB-ACCESS-TIMESTAMP A timestamp for your request
    All request bodies should have content type application/json and be valid JSON.

    The CB-ACCESS-SIGN header is generated by creating a sha256 HMAC using the secret key on the prehash string
    timestamp + method + requestPath + body (where + represents string concatenation). The timestamp value is the same as the
    CB-ACCESS-TIMESTAMP header.

    The body is the request body string or omitted if there is no request body (typically for GET requests).

    The method should be UPPER CASE.

    The CB-ACCESS-TIMESTAMP header MUST be number of seconds since Unix Epoch.

    Your timestamp must be within 30 seconds of the api service time or your request will be considered expired and rejected.
    We recommend using the time endpoint to query for the API server time if you believe there many be time skew
    between your server and the API servers.

    """
    body = {}
    method = "GET"
    nonce = str(int(round(time.time() * 1000000)))
    requestPath = "/accounts"
    signature = f"{nonce}{method}{requestPath}{body}"
    h = hmac.new(settings.api.coinbase.api_secret.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
    sig = h.hexdigest()

    url = "https://api.coinbase.com/v2/accounts"
    cb_access_key = settings.api.coinbase.api_key
    cb_access_sign = sig
    cb_access_timestamp = nonce


def refresh_tblCurrencyExchangeRates():
    """Refresh Currency Exchange Rates table."""
    tbl = client.get_collection_view(settings.tables.tblCurrencyExchangeRates)

    # Get exchange rates from CNB
    rates = get_czk_exchange_rates()

    # Get table data
    table_rows = tbl.collection.get_rows()

    for row in table_rows:

        # Ignore empty rows if any
        if row.name == "":
            continue

        row.CZK = rates.get(row.name, 0)
        row.Date = rates['date']


def refresh_tblCryptoToUSD():
    tbl = client.get_collection_view(settings.tables.tblCryptoToUSD)

    tbl_rows = tbl.collection.get_rows()

    crypto_names = [row.title for row in tbl_rows]

    # Get exchange rates from
    rates = get_crypto_rates(crypto_names)

    for row in tbl_rows:
        row.USD = rates[row.title]['USD']
        row.CZK = rates[row.title]['CZK']


def refresh_degiro():
    """Refresh Degiro table."""

    # Get table from Degiro page
    notionTable = client.get_collection_view(settings.tables.stocks)

    # Pretty table settings
    x = PrettyTable()
    x.field_names = ["Code", "Investing URL", "USD", "Date"]
    # Column Alignment
    x.align["Code"] = "l"
    x.align["Investing URL"] = "l"
    x.align["USD"] = "r"
    x.align["Date"] = "r"

    # Get table data
    table_rows = notionTable.collection.get_rows()

    # Get all stock_tickers
    stock_tickers = " ".join([item.ticker for item in table_rows])
    df = yf.download(tickers=stock_tickers, period="2d", group_by="ticker", progress=False)

    tickers = yf.Tickers(stock_tickers)

    # Iterate over notion table rows
    for row in table_rows:

        # Ignore empty rows if any
        if row.ticker == "":
            continue

        ticker = tickers.tickers[row.ticker]

        shortName = ticker.info["shortName"]
        closing_value = round(df[row.ticker]["Close"][yesterday_date.strftime("%Y-%m-%d")], 2)

        print(f"Checking ticker: {row.ticker}: {closing_value}")

        # Update table USD, DATE fields with new values
        row.usd = closing_value
        row.name = shortName
        row.date = NotionDate(yesterday_date)

        # Add row to table for printing
        x.add_row([row.ticker, row.investing_url, row.usd, yesterday_date])

    print(x)


def get_czk_exchange_rates():
    """Get CZK eschange rates from CNB."""
    url = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"
    content = requests.get(url)
    data = content.text

    curdate = data.split("\n")[0].split()[0]
    curdate_as_date = datetime.strptime(curdate, "%d.%m.%Y")

    rates = {line.split('|')[3]: float(line.split('|')[4].replace(',', '.')) for line in data.split("\n")[3:] if line != ""}
    rates['date'] = curdate_as_date

    return rates


def get_crypto_rates(crypto_names: str):
    """Get crypto currency USD and CZK rates."""
    dc = {}
    for crypto_name in crypto_names:
        url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_name}&tsyms=USD,CZK"
        content = requests.get(url)
        data = content.json()
        dc[crypto_name] = data

    return dc


def refresh_degiroV2():
    """Hmm."""
    from degiro.degiro import degiro

    la = degiro()
    la.login('degiro/config.json')
    la.getConfig()
    pfs = la.getPortfolioSummary()
    portfolio = la.getPortfolio()
    total = pfs['equity']

    total = round(total, 0)

    tbl = PrettyTable()
    tbl.field_names = ["Symbol", "Product", "Size", "Price", "Subtotal", "Allocation"]
    tbl.align["Symbol"] = "r"
    tbl.align["Size"] = "r"
    tbl.align["Value"] = "r"
    tbl.align["Subtotal"] = "r"
    tbl.align["Allocation"] = "r"

    # Get table from Degiro page
    notionTable = client.get_collection_view(settings.tables.stocks)

    allo_sum = 0
    total2 = sum([row['size'] * row['price'] for row in portfolio['PRODUCT'].values()])
    for row in portfolio['PRODUCT'].values():
        subtot = round(row['size'] * row['price'], 2)
        alloc = (subtot / total2) * 100  # Asset allocation (%)
        allo_sum += round(alloc, 4)
        tbl.add_row([row['symbol'], row['name'], row['size'], row['price'], round(subtot, 1), round(alloc, 2)])

        symbol = row['symbol']
        result = round((row['price'] / row['breakEvenPrice']) - 1, 4)

        notionRow = notionTable.collection.get_rows(search=symbol)
        time.sleep(0.2)

        # Row with symbol found
        if notionRow.total != 0:
            notionRow = notionRow[0]
            print(f"Update! notionRow.name = {notionRow.name}")
            notionRow.name = row['name']
            notionRow.usd = row['price']
            notionRow.BEPrice = round(row['breakEvenPrice'], 2)
            notionRow.Currency = row['currency']
            notionRow.Result = result
            notionRow.Allocation = round(alloc / 100, 4)
            notionRow.Size = row['size']
            notionRow.SubTotal = subtot

        else:
            print(f"Add row: {row['symbol']}")
            newRow = notionTable.collection.add_row()
            newRow.ticker = row['symbol']
            newRow.name = row['name']
            newRow.usd = row['price']
            newRow.BEPrice = round(row['breakEvenPrice'], 2)
            newRow.Currency = row['currency']
            newRow.Result = result
            newRow.Allocation = round(alloc / 100, 4)
            newRow.Size = row['size']
            newRow.SubTotal = subtot

            result = notionTable.default_query().execute()

    print(tbl.get_string(sortby="Allocation", reversesort=True))
    print(table_footer(tbl, "Total", {'Subtotal': int(total), 'Allocation': f"{int(allo_sum)} %"}))

    # # Get table from Degiro page
    # notionTable = client.get_collection_view(settings.tables.stocks)
    # # Get table data
    # table_rows = notionTable.collection.get_rows()
    # # Iterate over rows
    # for row in table_rows:
    #     # Ignore empty rows if any
    #     if row.ticker == "":
    #         continue
    #     # Get the ticker
    #     ticker = row.ticker


def table_footer(tbl, text, dc):
    res = f"{tbl._vertical_char} {text}{' ' * (tbl._widths[0] - len(text))} {tbl._vertical_char}"

    for idx, item in enumerate(tbl.field_names):
        if idx == 0:
            continue
        if item not in dc.keys():
            res += f"{' ' * (tbl._widths[idx] + 1)} {tbl._vertical_char}"
        else:
            val = dc[item]
            if str(val).isnumeric():
                val = f"{val:,}"

            res += f"{' ' * (tbl._widths[idx] - len(str(val)))} {val} {tbl._vertical_char}"

    res += f"\n{tbl._hrule}"
    return res


def main():
    print("Starting...")

    # refresh_tblCryptoToUSD()
    # refresh_tblCurrencyExchangeRates()
    # refresh_degiro()  # Not done yet
    refresh_degiroV2()  # Not done yet
    # refresh_crypto()


if __name__ == "__main__":
    main()
