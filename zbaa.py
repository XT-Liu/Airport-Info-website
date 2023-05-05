import requests
import datetime
import time

class zbaaSpider:
    url = "https://www.bcia.com.cn/bcia/flight/flightInfo"
    cookie = '_ga=GA1.3.1342569734.1584717732; __utma=196169535.1342569734.1584717732.1585278217.1585278217.1; _gid=GA1.3.1833624172.1641391958; wzws_cid=b6bc3eb8bb400ee4f0a91ce0475df4ff435fd954f6a1ee5d1e2de3108f539145aaec03d246537767bd4680d417ced3acecaac49f716d4d349dc50bf42f949037295e63d8a5b3276ff0999ef8e6b6f3324a954cb1fd38046606d4330de88303dd6a1b4ed60dc00608b4a1783c538923f6'
    keyword = ''

    def __init__(self):
        return

    '''
        direction: 0出港 1进港
        date: -1昨天 0今天 1明天
    '''
    def get_flightlist(self, direction, date, keyword):
        url = self.url
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
        data = {
            'direction': direction,
            'con': keyword,
            'date': date,
            'time': -1
        }
        res = requests.post(url=url, headers=headers, data=data)
        res.encoding = "utf-8"
        js = res.json()
        flightlist_clear = []
        flightlist = js.get('flightList')
        # print("----------------------------------------------------------------------------------------------------------------------------------------------")
        if flightlist is None:
            return flightlist_clear, res.status_code
        '''
        for flight in flightlist:
            flight['sdt'] = datetime.datetime.fromtimestamp(flight['sdt'] / 1e3).strftime('%Y-%m-%d %H:%M:%S')[11:-3]  # 格式化时间戳
            flightlist_clear.append(flight)
        '''

        for flight in flightlist:
            if flight['flightNo'].find(' ') != -1:  # 剔除代码共享航班
                flightlist.remove(flight)
            else:
                flight['sdt'] = datetime.datetime.fromtimestamp(flight['sdt'] / 1e3).strftime('%Y-%m-%d %H:%M:%S')[
                                11:-3]  # 格式化时间戳
                flightlist_clear.append(flight)
        return flightlist_clear, res.status_code


if __name__ == '__main__':
    spider = zbaaSpider()
    flightlist, status_code = spider.get_flightlist(direction=0, date=0, keyword='')
    #print(len(flightlist), status_code)