import flask
from flask import render_template
from app import app
import asyncio
import platform
import sys
import pandas as pd
from bleak import BleakClient
import io
import time
import datetime
import math

pd.options.mode.chained_assignment = None

FILENAME = "./output.xlsx"
ADDY = (
    "DA:D3:CD:7E:F0:A8"
    if platform.system() != "SparkFun_nRF52840"
    else "00001523-1212-EFDE-1523-785FEABCD123"
)

TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

pressPoints = []
stringpressPoints = []
lenlist = 0
buflen = 400

def callback(sender: int, data: bytearray):
    pressPoints.append(data)
    datastring = data.decode("utf-8")
    stringpressPoints.append(datastring)
    global lenlist
    lenlist = len(stringpressPoints)

    errlist = ['11', 'xx', '00', '01', '02', '03', '04', '05', '06', '07']
    if lenlist > 1:
        if datastring[0:2] in errlist:
            if datastring == errlist[0]:
                if stringpressPoints[lenlist - 2][0:2] != errlist[9]:
                    newstring = errlist[9] + ' 0'
                    stringpressPoints.insert(lenlist- 1, newstring)
            for i in range(1,10):
                if datastring[0:2] == errlist[i]:
                    if stringpressPoints[lenlist -2][0:2] != errlist[i-1]:
                        newstring = errlist[i-1] + ' 0'
                        stringpressPoints.insert(lenlist - 1 , newstring)


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home(data=None):
    return flask.render_template('home.html')

@app.route('/dash', methods=['GET', 'POST'])
def dashboard(data=None):
    excel_data_df = pd.read_csv('/Users/alejandramoreno/Documents/Code/capstone2022/SmartSoleBackend/app/resources/finaltest_1.csv')
    convert_dict = {'x': int,
                    'y': int,
                    'd': int,
                    'r': int}
    excel_data_df = excel_data_df.astype(convert_dict)
    json_str = excel_data_df.to_json()
    return flask.render_template('heatmap.html', smartSoleData=json_str)

@app.route('/health', methods=['GET', 'POST'])
def pronation(data=None):
    return flask.render_template('health.html')

@app.route('/dataCollect', methods=['GET', 'POST'])
async def datCollect(data=None):
    async with BleakClient(ADDY) as client:
        if (client.is)
        await client.start_notify(TX_UUID, callback)

        global lenlist
        list_end = buflen * 10
        while lenlist < list_end:
            await client.read_gatt_char(TX_UUID)

        targetindex = stringpressPoints.index('11')
        finallist = stringpressPoints[targetindex:]
        finallist = [finallist[i:i+10] for i in range(0,len(finallist), 10)]
        df = pd.DataFrame(finallist, columns=['Del', 'time', 'chanel 0', 'channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7'])

        x = datetime.datetime.now()
        date = str(x.date())
        time = str(x.time())
        filename = str('SmartSole' + date + '_' + time[0:2] + 'h' + time[3:5] + 'm.csv')

        data = df
        # fix channel 1 spelling on both ends
        columns = ['channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7']
        final_col = ['channel 7', 'channel 6', 'channel 1', 'channel 5', 'channel 2', 'channel 3', 'channel 4']
        limit = [60, 68, 64, 66, 59, 70]
        needed = {}
        final = {}
        val = {}
        rad = {}

        data = data.astype(str)  # change all data points to strings

        data['time'] = data['time'].str[2:]  # remove the xx from the time values
        data['time'] = data['time'].astype(int)
        totaltime = (data['time'][len(data['time']) - 1] - data['time'][0]) / 1000  # total time in seconds

        # use this for loop to take the channel values off each number so we have just the data left
        for x in columns:
            data[x] = data[x].str[3:]
            for y in range(len(data[x])):
                data[x][y] = float(data[x][y])

        # above is only possible if the channel is retained even when a 0 is placed
        find_start = data['time'][0] + 4700
        cutoff = (data.iloc[(data['time'] - find_start).abs().argsort()[:1]]).index  # about 4.7 seconds in
        data = data.drop(data.index[0:cutoff[0]])  # cut first 5 seconds

        first = (data['channel 4'] >= 66).idxmax()  # get index of start of step 1

        # get index of first num >70 in channel 6
        for index, item in enumerate(data['channel 6']):
            if (item > 70):
                if ((index + cutoff[0]) > first):
                    break
                if ((index + cutoff[0]) < first):
                    pass

        # get index (x) of last num >70 in channel 6 --> for usage, need last -1
        for last in range((index + cutoff[0]), (index + cutoff[0] + 35)):
            if data['channel 6'][last] < 70:
                break
        step_time = (data['time'][last] - data['time'][first])/1000

        drange = (last + 1) - first
        div1 = math.ceil(drange / 3)
        div3 = math.ceil((drange - div1) / 2)
        div2 = drange - (div1 + div3)

        # get dictionary of only necessary values
        for x in columns:
            needed.setdefault(x, [])
            for y in range(first, last + 1):
                needed[x].append(data[x][y])

        # get the average for each of the three phases
        for x in columns:
            final.setdefault(x, [])
            final[x].append(((sum(needed[x][0:div1])) / div1))
            final[x].append((sum(needed[x][div1:div1 + div2]) / div2))
            final[x].append(((sum(needed[x][div1 + div2:div1 + div2 + div3])) / div3))

        send = pd.DataFrame(columns=['x', 'y', 'd', 'r', 't'])
        send['x'] = [170, 90, 180, 80, 150, 80, 120, 350, 420, 350, 420, 380, 420, 390,
                     170, 90, 180, 80, 150, 80, 120, 350, 420, 350, 420, 380, 420, 390,
                     170, 90, 180, 80, 150, 80, 120, 350, 420, 350, 420, 380, 420, 390]
        send['y'] = [60, 120, 200, 270, 350, 420, 510, 60, 120, 200, 270, 350, 420, 510,
                     60, 120, 200, 270, 350, 420, 510, 60, 120, 200, 270, 350, 420, 510,
                     60, 120, 200, 270, 350, 420, 510, 60, 120, 200, 270, 350, 420, 510]

        send['t'] = pd.Series([totaltime, step_time])

        for x in columns:
            val.setdefault(x, [])
            rad.setdefault(x, [])
            for y in range(0, 3):
                if final[x][y] >= 95:
                    val[x].append(100)
                    rad[x].append(85)
                if 80 <= final[x][y] < 95:
                    val[x].append(95)
                    rad[x].append(70)
                if 72 <= final[x][y] < 80:
                    val[x].append(87)
                    rad[x].append(65)
                if 65 <= final[x][y] < 72:
                    val[x].append(80)
                    rad[x].append(60)
                if 60 <= final[x][y] < 65:
                    val[x].append(80)
                    rad[x].append(55)
                if final[x][y] < 60:
                    val[x].append(75)
                    rad[x].append(50)

        c = 14
        i = 0
        for col in final_col:
            for x in range(0, 3):
                send['d'][x * c + i] = val[col][x]
                send['r'][x * c + i] = rad[col][x]
            i = i + 1

        c = 14
        i = 7
        for col in final_col:
            for x in range(0, 3):
                send['d'][x * c + i] = val[col][x]
                send['r'][x * c + i] = rad[col][x]
            i = i + 1

        send.to_csv("finaltest_JULIAVIDEO.csv")

