#!/usr/bin/env python3

from config import settings
from notion.client import NotionClient
from prettytable import PrettyTable
import yfinance as yf


def main():
    print("This is main")
    # data = yf.download(tickers="AMD MNKD", period="1d", group_by="tickers")
    # print(data)

    client = NotionClient(token_v2=settings.token)

    degiro = client.get_collection_view(settings.stocks_site)
    print(f"Degiro: {degiro}")

    x = PrettyTable()
    x.field_names = ["Code", "Investing URL", "Price"]

    for row in degiro.collection.get_rows(search=""):
        if row.stock_name == "":
            continue

        stock = yf.Ticker(row.stock_name)
        price = stock.info["regularMarketPrice"]
        row.price = price

        # Add to table for printing
        x.add_row([row.stock_name, row.investing_url, row.price])

    print(x)


if __name__ == "__main__":
    main()
