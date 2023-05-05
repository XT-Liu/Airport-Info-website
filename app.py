from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, update, not_
from flask_migrate import Migrate
from zbaa import zbaaSpider
import datetime, time
import schedule
import threading

#阿里云VNC密码 Lxt666
#ECS服务器密码 Lxt362569

app = Flask(__name__)
spider = zbaaSpider()

#MySQL所在的主机名
HOSTNAME = "127.0.0.1"
#MySQL监听的端口号，默认3306
PORT = '3306'
#链接MySQL的用户名、密码
USERNAME = "root"
PASSWORD = "0308"                                                     #上传服务器之前把密码去掉
#MySQL上创建的数据库名称
DATABASE = "flight_database"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
'''
with app.app_context():
    with db.engine.connect() as conn:
        rs = conn.execute("select 1")
        print(rs.fetchone())
'''

class FlightlistUpdateTime(db.Model):
    __tablename__ = "FlightlistUpdateTime"
    table = db.Column(db.String(100, collation='utf8_general_ci'), primary_key=True)
    updatetime = db.Column(db.String(100, collation='utf8_general_ci'))

class BaseFlightTable(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, autoincrement=True)
    showtime = db.Column(db.String(100, collation='utf8_general_ci'))
    airline = db.Column(db.String(100, collation='utf8_general_ci'))
    flightnumber = db.Column(db.String(100, collation='utf8_general_ci'), primary_key=True)
    start_or_dest = db.Column(db.String(100, collation='utf8_general_ci'))
    aircrafttype = db.Column(db.String(100, collation='utf8_general_ci'))
    parkingbay = db.Column(db.String(100, collation='utf8_general_ci'))
    status = db.Column(db.String(100, collation='utf8_general_ci'))
class YesterdayInboundFlight(BaseFlightTable):
    __tablename__ = "YesterdayInboundFlight"
class TodayInboundFlight(BaseFlightTable):
    __tablename__ = "TodayInboundFlight"
class TomorrowInboundFlight(BaseFlightTable):
    __tablename__ = "TomorrowInboundFlight"
class YesterdayOutboundFlight(BaseFlightTable):
    __tablename__ = "YesterdayOutboundFlight"
class TodayOutboundFlight(BaseFlightTable):
    __tablename__ = "TodayOutboundFlight"
class TomorrowOutboundFlight(BaseFlightTable):
    __tablename__ = "TomorrowOutboundFlight"
db.create_all()

'''
    “更新时间表”初始化
'''
def updatetimeTableInit():
    count = db.session.query(FlightlistUpdateTime).count()
    if count == 0:    #如果“更新时间表”表项为空
        updatetime1 = FlightlistUpdateTime(table="YesterdayInboundFlight", updatetime="")
        updatetime2 = FlightlistUpdateTime(table="YesterdayOutboundFlight", updatetime="")
        updatetime3 = FlightlistUpdateTime(table="TodayInboundFlight", updatetime="")
        updatetime4 = FlightlistUpdateTime(table="TodayOutboundFlight", updatetime="")
        updatetime5 = FlightlistUpdateTime(table="TomorrowInboundFlight", updatetime="")
        updatetime6 = FlightlistUpdateTime(table="TomorrowOutboundFlight", updatetime="")
        db.session.add_all([updatetime1, updatetime2, updatetime3, updatetime4, updatetime5, updatetime6])
        db.session.commit()

'''
    获取数据库中各张表的更新时间
    参数：tablename-表名
'''
def renewUpdatetime(tablename):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_line = FlightlistUpdateTime.query.filter(FlightlistUpdateTime.table == tablename)
    update_line.updatetime = current_time
    stmt = update(FlightlistUpdateTime).where(FlightlistUpdateTime.table == tablename).values(
        updatetime=current_time)
    db.session.execute(stmt)
    db.session.commit()
    print(tablename+" updatetime renew")

'''
    获取数据库中各张表的更新时间
    参数：tablename-表名
'''
def getUpdatetime(tablename):
    line = db.session.query(FlightlistUpdateTime).filter_by(table=tablename).first()
    if line:
        update_time = line.updatetime
    else:
        update_time = "N/A"
    return update_time

'''
    更新表中的航班信息
    参数：table-查询的表，flightlist-最新爬取的航班列表
'''
def renewFlightinfo(table, flightlist):
    for flight in flightlist:
        if flight['startAirport']:    #判断进出港航班方向，提取不同参数作为location
            location = flight['startAirport'] + '/' + flight['startAirportCn']
        else:
            location = flight['dest'] + '/' + flight['destCn']
        query_flight = table.query.filter(
            table.flightnumber.contains(flight['flightNo'])).first()
        if query_flight:  # 如果数据库中有重复航班，则更新信息
            query_flight.id = flightlist.index(flight) + 1
            query_flight.showtime = flight['sdt']
            query_flight.airline = flight['airlineCn']
            query_flight.flightnumber = flight['flightNo']
            query_flight.aircrafttype = flight['airType']
            query_flight.start_or_dest = location
            query_flight.parkingbay = flight['park1']
            query_flight.status = flight['fliStruts']
        else:  # 如果数据库中未发现重复航班，则插入新航班
            add_flight = table(id=flightlist.index(flight) + 1, showtime=flight['sdt'],
                                                 airline=flight['airlineCn'], flightnumber=flight['flightNo'],
                                                 aircrafttype=flight['airType'],
                                                 start_or_dest=location,
                                                 parkingbay=flight['park1'],
                                                 status=flight['fliStruts'])
            db.session.add(add_flight)
        db.session.commit()

'''
    清空数据库中的航班信息
'''
def cleanFlightTable():
    db.session.query(YesterdayInboundFlight).delete()
    db.session.query(YesterdayOutboundFlight).delete()
    db.session.query(TodayInboundFlight).delete()
    db.session.query(TodayOutboundFlight).delete()
    db.session.query(TomorrowInboundFlight).delete()
    db.session.query(TomorrowOutboundFlight).delete()
    db.session.commit()

'''
    定时器监听
'''
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def queryWideBody(table):
    db_flight = table.query.filter(and_(or_(table.aircrafttype.contains("33"),
                                       table.aircrafttype.contains("34"),
                                       table.aircrafttype.contains("35"),
                                       table.aircrafttype.contains("388"),
                                       table.aircrafttype.contains("74"),
                                       table.aircrafttype.contains("76"),
                                       table.aircrafttype.contains("77"),
                                       table.aircrafttype.contains("78"),
                                       table.aircrafttype.contains("A4F"))
                                        )) \
        .order_by("showtime")
    return db_flight
def queryForeignAirline(table):
    db_flight = table.query.filter(not_(or_(table.airline.contains("中国国际航空有限公司"),
                                            table.airline.contains("中国东方航空有限公司"),
                                            table.airline.contains("中国南方航空有限公司"),
                                            table.airline.contains("海南航空股份有限公司"),
                                            table.airline.contains("深圳航空有限责任公司"),
                                            table.airline.contains("四川航空股份有限公司"),
                                            table.airline.contains("祥鹏航空"),
                                            table.airline.contains("大新华航空公司"),
                                            table.airline.contains("山东航空有限责任公司"),
                                            table.airline.contains("浙江长龙航空有限公司"),
                                            table.airline.contains("中国邮政航空公司"),
                                            table.airline.contains("顺丰航空有限公司"),
                                            table.airline.contains("西藏航空有限公司"),
                                            table.airline.contains("厦门航空有限公司"),
                                            table.airline.contains("昆明航空有限公司"),
                                            table.airline.contains("江西航空有限公司"))
                                        )) \
        .order_by("showtime")
    return db_flight
'''
    从MySQL中查询指定航班列表
    参数：table-查询的表，form-前端返回的查询条件表单
'''
def querySQL(table, form=None):
    show_flightlist = []
    # 若未收到表单数据
    if form == None:
        # 从数据库中查询当前所有航班
        print("receive a GET")
        db_flight = table.query.order_by("showtime")
    else:  # 收到了表单数据
        # 从数据库中查找指定航班
        print("receive a POST", form)

        if form['status'] == '1':   #仅查询未执行航班
            if not any([form['airline'], form['flightnumber'], form['aircrafttype'], form['location'],
                    form['parkingbay']]):
                db_flight = table.query.filter(or_(table.status.contains("预计"),table.status == None)) \
                    .order_by("showtime")
            else:
                db_flight = table.query.filter(and_(and_(table.airline.contains(form['airline']) if form['airline'] else True,
                        table.flightnumber.contains(form['flightnumber']) if form[
                            'flightnumber'] else True,
                        table.aircrafttype.contains(form['aircrafttype']) if form[
                            'aircrafttype'] else True,
                        table.start_or_dest.contains(form['location']) if form[
                            'location'] else True,
                        table.parkingbay.contains(form['parkingbay']) if form[
                            'parkingbay'] else True),
                                                    or_(table.status.contains("预计"),table.status == None))
                    ) \
                    .order_by("showtime")
        elif form['status'] == '2':
            db_flight = queryWideBody(table)
        elif form['status'] == '3':
            db_flight = queryForeignAirline(table)
        elif not any([form['airline'], form['flightnumber'], form['aircrafttype'], form['location'],
                    form['parkingbay']]):
            db_flight = table.query.order_by("showtime")
        else:
            db_flight = table.query.filter(
                and_(table.airline.contains(form['airline']) if form['airline'] else True,
                    table.flightnumber.contains(form['flightnumber']) if form[
                        'flightnumber'] else True,
                    table.aircrafttype.contains(form['aircrafttype']) if form[
                        'aircrafttype'] else True,
                    table.start_or_dest.contains(form['location']) if form[
                        'location'] else True,
                    table.parkingbay.contains(form['parkingbay']) if form[
                        'parkingbay'] else True)) \
                .order_by("showtime")

    for flight in db_flight:
        show_flight = {
            'sdt': flight.showtime,
            'airlineCn': flight.airline,
            'flightNo': flight.flightnumber,
            'airType': flight.aircrafttype,
            'start_or_dest': flight.start_or_dest,
            'park1': flight.parkingbay,
            'fliStruts': flight.status
        }
        show_flightlist.append(show_flight)
    return show_flightlist

@app.before_first_request
def schedule_tasks():
    # 在第一次请求前执行定时任务
    #cleanFlightTable()
    updatetimeTableInit()
    schedule.every().day.at('00:00').do(cleanFlightTable)  # 每天 24 点执行 cleanFlightTable 函数
    # 启动定时任务的线程
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/zbaa_yesterday_dep', methods=['GET', 'POST'])
def zbaa_yesterday_dep():
    tablename = "YesterdayOutboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=0, date=-1, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(YesterdayOutboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(YesterdayOutboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(YesterdayOutboundFlight, form)
    return render_template("zbaa_yesterday_dep.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

@app.route('/zbaa_yesterday_arr', methods=['GET', 'POST'])
def zbaa_yesterday_arr():
    tablename = "YesterdayInboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=1, date=-1, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(YesterdayInboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(YesterdayInboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(YesterdayInboundFlight, form)
    return render_template("zbaa_yesterday_arr.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

@app.route('/zbaa_today_dep', methods=['GET', 'POST'])
def zbaa_today_dep():
    tablename = "TodayOutboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=0, date=0, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(TodayOutboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(TodayOutboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(TodayOutboundFlight, form)

    return render_template("zbaa_today_dep.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

@app.route('/zbaa_today_arr', methods=['GET', 'POST'])
def zbaa_today_arr():
    tablename = "TodayInboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=1, date=0, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(TodayInboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(TodayInboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(TodayInboundFlight, form)
    return render_template("zbaa_today_arr.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

@app.route('/zbaa_tomorrow_dep', methods=['GET', 'POST'])
def zbaa_tomorrow_dep():
    tablename = "TomorrowOutboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=0, date=1, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(TomorrowOutboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(TomorrowOutboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(TomorrowOutboundFlight, form)
    return render_template("zbaa_tomorrow_dep.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

@app.route('/zbaa_tomorrow_arr', methods=['GET', 'POST'])
def zbaa_tomorrow_arr():
    tablename = "TomorrowInboundFlight"
    flightlist, status_code = spider.get_flightlist(direction=1, date=1, keyword='')
    is_renew = False
    if status_code == 200:
        if len(flightlist) > 0:
            renewUpdatetime(tablename)
            is_renew = True
        renewFlightinfo(TomorrowInboundFlight, flightlist)

    if request.method == "GET":
        show_flightlist = querySQL(TomorrowInboundFlight)
    else:
        form = request.form
        show_flightlist = querySQL(TomorrowInboundFlight, form)
    return render_template("zbaa_tomorrow_arr.html", flightlist=show_flightlist, update_time=getUpdatetime(tablename), is_renew=is_renew)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



