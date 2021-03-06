#!/usr/bin/env python
import eventlet
eventlet.monkey_patch()
import json
import pandas as pd
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, disconnect
#from random 
import random
import numpy as np

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
# Personally, I install and use eventlet


#Read ticker to DataFrame
filePath = './data/Volume_Spike_Last_30D_1M_List.xlsx'
dfA = pd.read_excel(filePath, sheet_name='Sheet1')


#async_mode = None
async_mode = 'eventlet'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()






# The websocket is maintained in the background, and this
# function outputs a random number every 5 seconds
def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        #socketio.sleep(5)
        socketio.sleep(1)
        count += 1
        #number = round(random()*10, 3)
        number = round(random.uniform(-1,1)*10, 3)
        socketio.emit('my_response',
                      {'data': number, 'count': count},
                      namespace='/test')


# The websocket is maintained in the background, and this
# function outputs a random number every 5 seconds
def background_thread2():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        try:
            #socketio.sleep(5)
            socketio.sleep(1)
            count += 1
            #number = round(random()*10, 3)
            #number = round(random.uniform(-1,1)*10, 3)

            symbol = 'HK_Stock_Top20'
            dff = pd.read_csv('./data/{0}.csv'.format(symbol), header=None, names=['DateTime','Symbol','Last','Chg','Chg %','Volume','Turnover','P/E','Market Cap'])
            df = dff[['DateTime','Symbol','Last','Chg','Chg %','Volume','Turnover']].copy()
            df['Last'] = df['Last'].astype('float').round(3)
            df['Chg'] = df['Chg'].astype('float').round(3)
            df['Chg %'] = df['Chg %'].str.rstrip('%').astype('float').round(3)
            df['Ticker'] = df['Symbol'].str[1:]
            df = pd.merge(df, dfA, on=['Ticker'], how='left')
            #df = df.round({'Last': 3, 'Chg %': 3})
            dfB = df[['DateTime','Ticker','Symbol_y','Last','Chg','Chg %','Volume_x','Turnover']].copy()
            #dfB['Hit_Ticker'] = dfB['Symbol_y'].fillna('-', inplace=True)
            #dfB['Hit_Ticker'] = dfB['Symbol_y'].fillna('-')
            dfB['Hit_Ticker'] = dfB['Symbol_y'].replace(np.nan, '-')
            dfB['Volume'] = dfB['Volume_x']
            df = dfB[['DateTime','Ticker','Hit_Ticker','Last','Chg','Chg %','Volume','Turnover']].copy()
            #print(df)
            mydata = df.to_dict(orient='records')
            #mydata = df.to_json(orient='records')
            data = mydata
            #print(data)

            # other column settings -> http://bootstrap-table.wenzhixin.net.cn/documentation/#column-options
            columns = []
            for column in df.columns[0:]:
                col = {}
                col["field"] = column
                col["title"] = column
                col["sortable"] = True
                columns.append(col)
            #print(columns)


            socketio.emit('my_response',
                          {'data': data, 'columns':columns, 'count': count},
                          #{'data': number, 'count': count},
                          namespace='/test')

        except Exception as e:
            returnMsg = 'Error loading csv for {0}: {1}'.format(symbol, str(e))
            print('Error loading csv for {0}: {1}'.format(symbol, str(e)))




# Route for serving up the index page
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

# This function is called when a web browser connects
@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread2)
    emit('my_response', {'data': 'Connected', 'count': 0})

# Ping-pong allows Javascript in the web page to calculate the
# connection latency, averaging over time
@socketio.on('my_ping', namespace='/test')
def ping_pong():
    emit('my_pong')

# Notification that a client has disconnected
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


# Run the web app
if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5001)
