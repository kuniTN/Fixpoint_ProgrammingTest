# -*- coding: utf-8 -*-
from ipaddress import ip_interface
import glob
import time
import threading
import os
import datetime

ServerState = []#[ip,state,number of Failure]
FailedServerLog = []#[ip,log...]
PrevReadFile = ''#読み込み済みファイル記録
PrevReadLine = 0#読み込み済み行記録
LatestCheck = '0'#最新読み込み確認日時

def createList(data):
    global ServerState,FailedServerLog
    ServerState.append([ip_interface(data),-1,0])
    FailedServerLog.append([ip_interface(data)])
    ServerState=sorted(ServerState,key=lambda x:x[0])
    FailedServerLog = sorted(FailedServerLog,key=lambda x:x[0])

def logFileSearch():#最新ファイルを探索
    FileName = glob.glob('*access.log')
    FileName = sorted(FileName,reverse=True)
    return FileName[0]

def logFileRead(fName):
    global PrevReadLine,ServerState,FailedServerLog,LatestCheck
    with open(fName,'r') as f:
        for l,line in enumerate(f):
            if l == PrevReadLine:
                data = line.strip().split(',')
                check = -1 #各種確認用
                for i in range(len(ServerState)):#監視対象サーバーに登録済みか確認
                    if data[1] == str(ServerState[i][0]):
                        check = i#登録済みであった場合
                        break
                if check == -1:#新規ipであった場合,リストを新規作成　
                    createList(data[1])
            #ここから状態判定
                for i in range(check,len(ServerState)):#もし前のfor文で探索済みで追加されていない場合はソートが起きていないため，初回ループで処理が開始
                    if data[1] == str(ServerState[i][0]):#ファイルデータがある場所を参照
                        if data[2] == '-' and ServerState[i][1] != 0: #現在タイムアウトで前回通信できていた場合
                            ServerState[i][1] = 0 #statusを故障とする
                            ServerState[i][2] += 1 #故障回数+1
                            FailedServerLog[i].append(data[0])
                        elif data[2] != '-':
                            if ServerState[i][1] == 0:#前回は故障状態だったが通信が回復した場合
                                FailedServerLog[i][ServerState[i][2]] += data[0]#回復時刻を付加
                            ServerState[i][1] = 2 #statusを通信可能状態とする
                        break
                PrevReadLine += 1
                LatestCheck = data[0]

def logFileControl():
    global PrevReadLine,PrevReadFile
    TargetFileName = logFileSearch()
    if TargetFileName != PrevReadFile:
        PrevReadLine = 0
        PrevReadFile = TargetFileName
    logFileRead(TargetFileName)
    
def Print(data):
    with open('log.txt','a') as f:
        print(data)
        print(data,file = f)
        
def show():
    open('log.txt','w').close
    os.system('cls')
    print("If you want to stop the program, press Ctrl + C")
    if LatestCheck != '0':
        currentDate=datetime.datetime.strptime(LatestCheck,"%Y%m%d%H%M%S")
        Print ("Last Check : " + str(currentDate))
    Print('-----------------------')
    Print('Detected failure server')
    for i in range(len(ServerState)):
        if ServerState[i][2] != 0:#故障判断歴が1回でもある場合
            state = ' '
            if ServerState[i][1]==0:
                state = ' *'
            Print(state+str(ServerState[i][0]))
            for j in range(ServerState[i][2]):
                d1 = datetime.datetime.strptime(FailedServerLog[i][j+1][:14],"%Y%m%d%H%M%S")
                d2 = ""
                if len(FailedServerLog[i][j+1])>14:
                    d2 = datetime.datetime.strptime(FailedServerLog[i][j+1][14:],"%Y%m%d%H%M%S")
                    d2 = " -> Rediscovery : " + str(d2) + "  Failure period : " + str(d2-d1)
                else:
                    d2 = "    elapsed time : " +str(currentDate-d1)
                Print ("     ping TimeOut : " +str(d1) + str(d2))


def Worker():
    logFileControl()
    show()
        
def Scheduler(interval,func):
    BaseTime = time.time()
    NextTime = 0
    while True:
        t = threading.Thread(target=func)
        t.start()
        t.join()
        NextTime = ((BaseTime-time.time())%interval) or interval
        time.sleep(NextTime)
        
try:
    Scheduler(1,Worker)
    
except KeyboardInterrupt:
    print("Program ended.")      