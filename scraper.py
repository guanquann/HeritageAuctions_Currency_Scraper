import time
import config
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup


def params_for_page(n, url_id):
    # e.g: https://currency.ha.com/c/search-results.zx?No=0&N=790+231+56+1958+1219
    return (
        ('No', n),
        ('N', '790 231 56 1958 {}'.format(url_id)),
    )


def scrape_website(output, currency, url_id):
    description_list = []
    link_list = []
    auction_list = []
    lot_list = []
    date_list = []
    sold_amount_list = []

    n = 0
    while True:
        params = params_for_page(n, url_id)
        response = requests.get('https://currency.ha.com/c/search-results.zx',
                                headers=config.headers,
                                params=params,
                                cookies=config.cookies
                                )
        html_txt = BeautifulSoup(response.text, "html.parser")

        list_of_items = html_txt.findAll("li", {"class": "item-block gallery"})
        for i in list_of_items:
            # Check that element has child
            if i.find("a"):
                link_list.append(i.findAll("a")[1]["href"])
                description_list.append(i.findAll("a")[1].find("b").text.replace("\n", " "))

                lotno = i.find("div", {"class": "lotno"}).text.replace("\n", "").split(" | ")
                auction_list.append(lotno[0].split()[1])
                lot_list.append(lotno[1].split()[1])
                date_list.append(lotno[2].rsplit(" ", 1)[0])

                try:
                    sold_amount = i.find("div", {"class": "current-amount"}).find("strong").text
                except AttributeError:
                    sold_amount = "N/A"
                sold_amount_list.append(sold_amount)

        # Check to see if there are any new pages
        pageindex = html_txt.findAll("a", {"class": "pageindex"})
        second_last_href_link = int(pageindex[-2]["href"].split("No=")[1].split("&")[0])
        last_href_link = int(pageindex[-1]["href"].split("No=")[1].split("&")[0])
        if last_href_link > second_last_href_link:
            print("Scraping completed!")
            print("*" * 100)
            break
        else:
            n += 204
        time.sleep(0.5)

    df = pd.DataFrame.from_dict({"Description": description_list,
                                 "URL": link_list,
                                 "Auction": auction_list,
                                 "Lot": lot_list,
                                 "Date": date_list,
                                 "Amount": sold_amount_list})
    df["Currency"] = currency
    df.loc[df["Description"].str.contains("1918"), "Year"] = "1918"
    df.loc[df["Description"].str.contains("1928"), "Year"] = "1928"
    df.loc[df["Description"].str.contains("1934"), "Year"] = "1934"
    df.loc[df["Description"].str.contains("1934A"), "Year"] = "1934A"
    df.to_csv(output, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Heritage Auctions Currency Scraper')
    parser.add_argument('--output_filename',
                        default="output.csv",
                        type=str,
                        help='Export file name')
    parser.add_argument('--denominator',
                        default=500,
                        choices=[500, 1000],
                        type=int,
                        help='Denominator you wish to scrape')
    args = parser.parse_args()

    # keys: currency denominator; values: url id of website
    # e.g: https://currency.ha.com/c/search-results.zx?No=0&N=790+231+56+1958+1219
    currency_mapping_dict = {500: 1219, 1000: 1218}
    output_filename = args.output_filename
    denominator = args.denominator
    url = currency_mapping_dict[denominator]
    print("Saving to: {}\nDenominator: ${}\nWebsite ID: {}".format(output_filename, denominator, url))

    scrape_website(output_filename, denominator, url)
