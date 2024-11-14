from collections import Counter

import requests


def get_most_relevant_concept(concepts: list):
    cnames = [i["concept"] for i in concepts]
    counter = Counter(cnames)
    most_common_cname, _ = counter.most_common(1)[0]
    score_average = [
        i["distance"]
        for i in concepts
        if i["concept"] == most_common_cname
    ]
    score_average = sum(score_average) / len(score_average)
    return most_common_cname, score_average


def fetch_concept_info() -> list:
    host = "https://t-flashnews.kuai008.cn/api/client-api/concept-manifest/10jqka-not-encrypted"
    params = {
        "current": 1,
        "pageSize": 1,
        "acctoken": "-3-copilot@1189f930-09xx-4cc8-bxx8-e15cf93d40f6",
    }
    try:
        resp = requests.get(host, params=params).json()
        params["pageSize"] = resp["total"]
        resp = requests.get(host, params=params).json()
        data = resp["data"]
    except Exception:
        __import__("traceback").print_exc()
    return data


def fetch_stock_info(concept_id: int) -> list:
    data = []
    host = f"https://t-flashnews.kuai008.cn/api/client-api/concept-manifest/10jqka-not-encrypted/{concept_id}"
    params = {"acctoken": "-3-copilot@1189f930-09xx-4cc8-bxx8-e15cf93d40f6"}
    try:
        data = requests.get(host, params=params).json()
    except Exception:
        __import__("traceback").print_exc()
    return data


def get_concept_stocks():
    records = fetch_concept_info()
    data = []
    for record in records:
        stocks = fetch_stock_info(record["id"])
        leader_stock_codes = [i["code"] for i in record["leaders"]]
        stocks = [
            {"is_leader": True, **stock}
            for stock in stocks
            if stock["stockCode"] in leader_stock_codes
        ] + [
            {"is_leader": False, **stock}
            for stock in stocks
            if stock["stockCode"] not in leader_stock_codes
        ]
        data.append({
            "concept_id": record["id"],
            "concept_name": record["name"],
            "definition": record["definition"],
            "stocks": stocks
        })
    records = [
        {
            "id": concept["concept_id"],
            "name": concept["concept_name"],
            "definition": concept["definition"],
            "stock_code": stock["stockCode"],
            "stock_name": stock["stockName"],
            "reason": stock["conceptExplain"]
        }
        for concept in data 
        for stock in concept["stocks"]
    ]
    return records


if __name__ == "__main__":
    data = get_concept_stocks()
