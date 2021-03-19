import re
from datetime import datetime
import pandas as pd


def conditional_search(json_load, dt_from, dt_to):
    send = []
    for i in range(json_load['hit_number']):
        pub_date = json_load['results'][i]['published']
        pub_date = pd.to_datetime(pub_date, utc=True)
        dt_from = pd.to_datetime(dt_from, utc=True)
        dt_to = pd.to_datetime(dt_to, utc=True)
        # もしも期間内であったら追加
        if dt_from <= pub_date <= dt_to:
            send.append(json_load['results'][i])

    # フロント側が受け取りやすい形で出す
    result_format = {
        'hit_number': len(send),
        'results': send,
        'elapsed_days': 0
    }

    return result_format
