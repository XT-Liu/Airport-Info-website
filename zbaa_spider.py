import requests
import json
import xlwt
import datetime
import time

def get_flightlist(url, cookie, direction, date, keyword):
    url = url
    headers = {
        'Cookie' : cookie,
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
    #print("----------------------------------------------------------------------------------------------------------------------------------------------")
    if flightlist is None:
        return flightlist_clear
    '''
    for flight in flightlist:
        flight['sdt'] = datetime.datetime.fromtimestamp(flight['sdt'] / 1e3).strftime('%Y-%m-%d %H:%M:%S')[11:-3]  # 格式化时间戳
        flightlist_clear.append(flight)
    '''

    for flight in flightlist:
        if flight['flightNo'].find(' ') != -1:                         #剔除代码共享航班
            flightlist.remove(flight)
            #print("-----------删除-----------", flight['flightNo'])
        else:
            flight['sdt'] = datetime.datetime.fromtimestamp(flight['sdt']/1e3).strftime('%Y-%m-%d %H:%M:%S')[11:-3] #格式化时间戳
            flightlist_clear.append(flight)
            #print(json.dumps(flight['flightNo'], indent=4, ensure_ascii=False))

    #input()
    return flightlist_clear

def save_as_json(jsonpath, list, direction):
    if direction == 0:
        path = jsonpath + '\\json\\dp.json'
    else:
        path = jsonpath + '\\json\\ar.json'
    with open(path, 'w') as f:
        json.dump(list, f)
    return path

def save_as_xls(xlspath, dp_jsonpath, ar_jsonpath, date, key):
    wb = xlwt.Workbook(encoding= 'utf-8')
    dp_sht = wb.add_sheet('出发')
    ar_sht = wb.add_sheet('到达')

    dp_sht.write(0, 0, '计划离港时间')
    dp_sht.col(0).width = 3200
    dp_sht.write(0, 1, '航空公司')
    dp_sht.col(1).width = 6500
    dp_sht.write(0, 2, '航班号')
    dp_sht.write(0, 3, '机型')
    dp_sht.write(0, 4, '目的地')
    dp_sht.col(4).width = 5000
    dp_sht.write(0, 5, '航站楼')
    dp_sht.write(0, 6, '机位')
    dp_sht.write(0, 7, '状态')
    dp_sht.col(7).width = 4500

    ar_sht.write(0, 0, '计划抵达时间')
    ar_sht.col(0).width = 3200
    ar_sht.write(0, 1, '航空公司')
    ar_sht.col(1).width = 6500
    ar_sht.write(0, 2, '航班号')
    ar_sht.write(0, 3, '机型')
    ar_sht.write(0, 4, '出发地')
    ar_sht.col(4).width = 5000
    ar_sht.write(0, 5, '航站楼')
    ar_sht.write(0, 6, '机位')
    ar_sht.write(0, 7, '状态')
    ar_sht.col(7).width = 4500

    with open(dp_jsonpath, 'r') as f1:
        dp_flightlist = json.load(f1)
    with open(ar_jsonpath, 'r') as f1:
        ar_flightlist = json.load(f1)

    ticks = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    val1 = 1
    for flight in dp_flightlist:
        if flight['fliStruts'] is not None and '取消' in flight['fliStruts']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour rose', 'borders: top 1, bottom 1, left 1, right 1')
        elif flight['fliStruts'] is not None and '延误' in flight['fliStruts']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow', 'borders: top 1, bottom 1, left 1, right 1')
        elif key != '' and key in flight['airlineCn']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour ice_blue', 'borders: top 1, bottom 1, left 1, right 1')
        else:
            style = xlwt.easyxf('borders: top 1, bottom 1, left 1, right 1')
        dp_sht.write(val1, 0, flight['sdt'], style)
        dp_sht.write(val1, 1, flight['airlineCn'], style)
        dp_sht.write(val1, 2, flight['flightNo'], style)
        dp_sht.write(val1, 3, flight['airType'], style)
        dp_sht.write(val1, 4, flight['dest'] + '/' + flight['destCn'], style)
        dp_sht.write(val1, 5, 'T' + flight['term1'], style)
        dp_sht.write(val1, 6, flight['park1'], style)
        dp_sht.write(val1, 7, flight['fliStruts'], style)
        val1 += 1
    dp_sht.write(0, 10, '数据更新时间:' + ticks)
    dp_sht.write(1, 10, '离港架次:' + str(val1-1))
    val2 = 1
    for flight in ar_flightlist:
        if flight['fliStruts'] is not None and '取消' in flight['fliStruts']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour rose', 'borders: top 1, bottom 1, left 1, right 1')
        elif flight['fliStruts'] is not None and '延误' in flight['fliStruts']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow',
                                'borders: top 1, bottom 1, left 1, right 1')
        elif key != '' and key in flight['airlineCn']:
            style = xlwt.easyxf('pattern: pattern solid, fore_colour ice_blue',
                                'borders: top 1, bottom 1, left 1, right 1')
        else:
            style = xlwt.easyxf('borders: top 1, bottom 1, left 1, right 1')
        ar_sht.write(val2, 0, flight['sdt'], style)
        ar_sht.write(val2, 1, flight['airlineCn'], style)
        ar_sht.write(val2, 2, flight['flightNo'], style)
        ar_sht.write(val2, 3, flight['airType'], style)
        ar_sht.write(val2, 4, flight['startAirport'] + '/' + flight['startAirportCn'], style)
        ar_sht.write(val2, 5, 'T' + flight['term1'], style)
        ar_sht.write(val2, 6, flight['park1'], style)
        ar_sht.write(val2, 7, flight['fliStruts'], style)
        val2 += 1
    ar_sht.write(0, 10, '数据更新时间:' + ticks)
    ar_sht.write(1, 10, '进港架次:' + str(val2-1))

    if date == -1:
        path = xlspath + 'flight_info\\zbaa_yesterday.xls'
    elif date == 0:
        path = xlspath + 'flight_info\\zbaa_today.xls'
    else:
        path = xlspath + 'flight_info\\zbaa_tomorrow.xls'
    wb.save(path)
    if date == -1:
        print('昨日航班更新ok，进港共' + str(val1-1) + '架次；离港共' + str(val2-1) +'架次')
    elif date == 0:
        print('今日航班更新ok，进港共' + str(val1-1) + '架次；离港共' + str(val2-1) +'架次')
    else:
        print('明日航班更新ok，进港共' + str(val1-1) + '架次；离港共' + str(val2-1) +'架次')
    return path

def request_flight_info(url, cookie, date, keyword):
    dp_flightlist = get_flightlist(url=url, cookie=cookie, direction=0, date=date, keyword=keyword)
    ar_flightlist = get_flightlist(url=url, cookie=cookie, direction=1, date=date, keyword=keyword)
    #print(json.dumps(dp_flightlist, indent=4, ensure_ascii=False))
    #print(json.dumps(ar_flightlist, indent=4, ensure_ascii=False))
    savepath = './'
    dp_jsonpath = save_as_json(savepath, dp_flightlist, direction=0)
    ar_jsonpath = save_as_json(savepath, ar_flightlist, direction=1)
    xlspath = save_as_xls(savepath, dp_jsonpath, ar_jsonpath, date=date, key='空港')
    return (dp_flightlist, ar_flightlist)

url = "https://www.bcia.com.cn/bcia/flight/flightInfo"
cookie = '_ga=GA1.3.1342569734.1584717732; __utma=196169535.1342569734.1584717732.1585278217.1585278217.1; _gid=GA1.3.1833624172.1641391958; wzws_cid=b6bc3eb8bb400ee4f0a91ce0475df4ff435fd954f6a1ee5d1e2de3108f539145aaec03d246537767bd4680d417ced3acecaac49f716d4d349dc50bf42f949037295e63d8a5b3276ff0999ef8e6b6f3324a954cb1fd38046606d4330de88303dd6a1b4ed60dc00608b4a1783c538923f6'
keyword = ''
if __name__ == '__main__':
    yes_dp_flight, yes_ar_flight = request_flight_info(url=url, cookie=cookie, date=-1, keyword=keyword)
    tod_dp_flight, tod_ar_flight = request_flight_info(url=url, cookie=cookie, date=0, keyword=keyword)
    tom_dp_flight, tom_ar_flight = request_flight_info(url=url, cookie=cookie, date=1, keyword=keyword)
    print("-------------数据更新完成--------------")