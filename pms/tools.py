from enum import Enum
from typing import List

import requests
from langchain_core.tools import StructuredTool
from openai import BaseModel

from config import url_entries, url_positions


class StrategyConstraint(Enum):
    MINUS_10 = "minus_10",
    MINUS_5 = "minus_5",



class TickerInfoItem(BaseModel):
    ticker: str

class StrategyDescription(BaseModel):
    ticker_type: str = "dollars_average_quarterly"
    ticker_info: List[TickerInfoItem]
    start_date: str
    amount: int



def set_display_type(display_type: str):
    return {"type": "display", "display_type": display_type}



def get_quarterly_dollar_average_strategy_info(tickers_info_item: StrategyDescription):


    return load_positions(tickers_info_item)

def load_positions(tickers_info_item):
    payload = {"content": tickers_info_item.dict()}
    response = requests.post(url_entries, json=payload)
    payload = {"content": response.json()}
    response = requests.post(url_positions, json=payload)
    response_json = response.json()
    # Ajouter un nouvel attribut à l'objet JSON
    response_json["type"] = "portfolio"
    response_json["display_type"] = "returns"
    return response_json


quarterly_dollar_average_strategy = StructuredTool.from_function(
    func=get_quarterly_dollar_average_strategy_info,
    name="financial_strategy_executor",
    description="Based on a quarterly dollar average  strategy, a list of quotes, "
                "a starting date and an amount to invest, generates entries.",
    return_direct=True
    # coroutine= ... <- you can specify an async method if desired as well
)


set_display = StructuredTool.from_function(
    func=set_display_type,
    name="set_display_type",
    description="Configure the data type displayed in the chart, one of : "
                "'''returns''','''valorisation''','''cma'''",
    return_direct=True
    # coroutine= ... <- you can specify an async method if desired as well
)