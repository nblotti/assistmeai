
import numpy
import pandas as pd
import requests
from djangoProject import config as cfg
from djangoProject.config import eod_server


class EodDataRepository:
    # class variable

    def __init__(self):

        self.eod_quote_url = eod_server+"eod/{0}.{1}?api_token={2}&from={3}&to={4}&fmt=json"
        self.eos_fundamentals_url = eod_server+("/fundamentals/{0}.{1}?api_token={2}&fmt=json&filter=Highlights,"
                                                "Valuation,Technicals,Earnings::trend,AnalystRatings")
    def get_eod_stock_data(self, ticker, market, from_date, to_date):

        result =  requests.get(self.eod_quote_url.format(ticker, market, cfg.EOD_API_KEY,from_date,to_date)).json()

        period = "A"
        delta = to_date - from_date
        delta_weeks = (numpy.floor(delta.days / 7))
        if 104 > delta_weeks > 12:
            period = "M"
        elif delta_weeks < 12:
            period = "W"


        df = pd.DataFrame(result)
        df["date_d"] = pd.to_datetime(df["date"])
        df.set_index('date_d', inplace=True)
        df.drop('high', axis=1, inplace=True)
        df.drop('low', axis=1, inplace=True)
        df.drop('open', axis=1, inplace=True)
        df.drop('close', axis=1, inplace=True)
        df.index = pd.to_datetime(df.index)

        df = df.resample(period).last()


        return df.to_json(orient = "records")
    def get_eod_fundamental_data(self, ticker, market):

        return requests.get(self.eos_fundamentals_url.format(ticker, market, cfg.EOD_API_KEY)).json()

