#!/usr/bin/env python3

import yfinance as yf

from datetime import datetime, timedelta
from notion.collection import NotionDate
from config import settings
from notion.client import NotionClient
from prettytable import PrettyTable


def main():
    print("Starting...")

    yesterday_date = datetime.now() - timedelta(1)

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
