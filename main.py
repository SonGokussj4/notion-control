#!/usr/bin/env python3

from config import settings
from notion.client import NotionClient
from prettytable import PrettyTable
import yfinance as yf


def main():
    print("Starting...")
    # data = yf.download(tickers="AMD MNKD", period="1d", group_by="tickers")

    client = NotionClient(token_v2=settings.token)

    # Get table from Degiro page
    tblDegiro = client.get_collection_view(settings.stocks_site)

    x = PrettyTable()
    x.field_names = ["Code", "Investing URL", "USD"]

    # Iterate over
    for row in tblDegiro.collection.get_rows(search=""):

        # Ignore empty rows if any
        if row.stock_name == "":
            continue

        # Get current stock price from Yahoo Finances
        stock = yf.Ticker(row.stock_name)
        price = stock.info["regularMarketPrice"]

        # Update table USD field with new price
        row.usd = price

        # Add row to table for printing
        x.add_row([row.stock_name, row.investing_url, row.usd])

    print(x)


if __name__ == "__main__":
    main()
