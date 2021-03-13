import re
from datetime import datetime


def conditional_search(json_load,dt_from,dt_to):
    send = []
    for i in range(json_load['hit_number']):
        pub_date = json_load['results'][i]['published']
        tz = re.findall('T.*Z',pub_date)
        pub_date = pub_date.replace(tz[0],'')
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d')
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