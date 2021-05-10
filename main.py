#!/usr/bin/env python3

import yfinance as yf

from datetime import datetime, timedelta
from notion.collection import NotionDate
from config import settings
from notion.client import NotionClient
from prettytable import PrettyTable
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

    client = NotionClient(token_v2=settings.token)

    # Get table from Degiro page
    tblDegiro = client.get_collection_view(settings.stocks_site)

    # Pretty table settings
    x = PrettyTable()
    x.field_names = ["Code", "Investing URL", "USD", "Date"]
    # Column Alignment
    x.align["Code"] = "l"
    x.align["Investing URL"] = "l"
    x.align["USD"] = "r"
    x.align["Date"] = "r"

    # Get table data
    table_rows = tblDegiro.collection.get_rows()

    # Get all stock_tickers
    stock_tickers = ' '.join([item.ticker for item in table_rows])
    df = yf.download(tickers=stock_tickers, period="2d", group_by="ticker", progress=False)

    tickers = yf.Tickers(stock_tickers)

    # Iterate over
    for row in table_rows:

        # Ignore empty rows if any
        if row.ticker == "":
            continue

        # print(f"Checking ticker: {row.ticker}: {closing_value}")
        ticker = tickers.tickers[row.ticker]

        shortName = ticker.info['shortName']
        closing_value = round(df[row.ticker]['Close'][yesterday_date.strftime("%Y-%m-%d")], 2)

        # Update table USD, DATE fields with new values
        row.usd = closing_value
        row.name = shortName
        row.date = NotionDate(yesterday_date)

        # Add row to table for printing
        x.add_row([row.ticker, row.investing_url, row.usd, yesterday_date])

    print(x)


if __name__ == "__main__":
    main()
