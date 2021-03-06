# -*- coding: utf-8 -*-
from ipaddress import ip_interface
import glob
import time
import threading
import os
import datetime


N = 5 #故障判断タイムアウト回数
m = 2 #サンプル数
t = 50 #平均応答時間閾値

ServerState = []#[ip,state,number of Failure,number of timeouts,average of ping,number of Overload]
FailedServerLog = []#[ip,log...]
ServerPingLog = []#[ip,log...]
OverloadServerLog = []#[ip,log...]
PrevReadFile = ''#読み込み済みファイル記録
PrevReadLine = 0#読み込み済み行記録
LatestCheck = '0'#最新読み込み確認日時


def createList(data):
    global ServerState,FailedServerLog,ServerPingLog,OverloadServerLog
    ServerState.append([ip_interface(data),-1,0,0,-1,0])
    FailedServerLog.append([ip_interface(data)])
    ServerPingLog.append([ip_interface(data)])
    OverloadServerLog.append([ip_interface(data)])
    ServerState=sorted(ServerState,key=lambda x:x[0])
    FailedServerLog = sorted(FailedServerLog,key=lambda x:x[0])
    ServerPingLog = sorted(ServerPingLog,key=lambda x:x[0])
    OverloadServerLog = sorted(OverloadServerLog,key=lambda x:x[0])

def logFileSearch():#最新ファイルを探索
    FileName = glob.glob('*access.log')
    FileName = sorted(FileName,reverse=True)
    return FileName[0]

def logFileRead(fName):
    global PrevReadLine,ServerState,FailedServerLog,OverloadServerLog,LatestCheck
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
                            ServerState[i][3] += 1
                            if ServerState[i][3]>=N:#故障判定
                                if ServerState[i][1] == 1: #過負荷状態であると判断されている場合
                                    OverloadServerLog[i][ServerState[i][5]] += data[0]#過負荷状態回復時刻を挿入
                                ServerState[i][1] = 0 #statusを故障とする
                                ServerState[i][2] += 1 #故障回数+1
                                ServerState[i][4] = -1 #平均応答時間を初期化　故障発生時には意味がなくなる
                                if len(ServerPingLog[i])>1:
                                    for j in range(1,len(ServerPingLog[i])):
                                        del ServerPingLog[i][1]#故障発生時，記録されているping値を消去
                                FailedServerLog[i].append(data[0])
                        elif data[2] != '-':
                            if ServerState[i][1] == 0:#前回は故障状態だったが通信が回復した場合
                                FailedServerLog[i][ServerState[i][2]] += data[0]#回復時刻を付加
                        
                            ServerState[i][3] = 0 #タイムアウトカウント数をリセット
                            ServerPingLog[i].append(int(data[2]))
                            if len(ServerPingLog[i]) >= m+1:
                                ServerState[i][4]=sum(ServerPingLog[i][1:])/m#m個のサンプルが集まった時，平均時間を計算し記録
                                if ServerState[i][4] > t and ServerState[i][1] == 2:#過負荷を新規検知した場合
                                    ServerState[i][1] = 1 #statusをOverloadとする
                                    ServerState[i][5] += 1 #Overload検知数を増やす
                                    OverloadServerLog[i].append(data[0])#過負荷検出時刻記録
                                elif ServerState[i][4] <= t and ServerState[i][1] == 1:#過負荷状態から回復した場合
                                    ServerState[i][1] = 2 #statusを通信可能状態とする.
                                    OverloadServerLog[i][ServerState[i][5]] += data[0]#過負荷状態回復時刻を挿入
                                del ServerPingLog[i][1]
                            else:
                                ServerState[i][1] = 2 #statusを通信可能状態とする.
                            
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
    Print("value of timeouts to be judged (N) : " + str(N))
    Print("value of counts of ping        (m) : " + str(m))
    Print("value of threshold of overload (t) : " + str(t))
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
    Print('------------------------')
    Print('Detected overload server')
    for i in range(len(ServerState)):
        if ServerState[i][5] != 0:#故障判断歴が1回でもある場合
            state = " "
            if ServerState[i][1]==1:
                state = " *"
            Print(state+str(ServerState[i][0]))
            for j in range(ServerState[i][5]):
                d1 = datetime.datetime.strptime(OverloadServerLog[i][j+1][:14],"%Y%m%d%H%M%S")
                d2 = ""
                if len(OverloadServerLog[i][j+1])>14:
                    d2 = datetime.datetime.strptime(OverloadServerLog[i][j+1][14:],"%Y%m%d%H%M%S")
                    d2 = " -> Recovery : " + str(d2) + "  Overload period : " + str(d2-d1)
                else:
                    d2 = "    elapsed time : " +str(currentDate-d1)
                Print ("     Overload detect : " +str(d1) + str(d2))
        
def set_N():
    global N
    os.system('cls')
    print("Input the value of timeouts to be judged as a failure")
    while True:
        buf = input()
        if buf.isdecimal():
            N=int(buf)
            break
        else:
            os.system('cls')
            print("Please input a numerical value.")
            print("Input the value of timeouts to be judged as a failure?")
def set_m():
    global m
    os.system('cls')
    print("Input the value of counts of ping")
    while True:
        buf = input()
        if buf.isdecimal():
            m=int(buf)
            break
        else:
            os.system('cls')
            print("Please input a numerical value.")
            print("Input the value of timeouts to be judged as a failure?")
def set_t():
    global t
    os.system('cls')
    print("Input the value of threshold of overload")
    while True:
        buf = input()
        if buf.isdecimal():
            t=int(buf)
            break
        else:
            os.system('cls')
            print("Please input a numerical value.")
            print("Input the value of timeouts to be judged as a failure?")

def Worker():
    logFileControl()
    show()
    #debug()
        
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
    set_N()
    set_m()
    set_t()
    Scheduler(1,Worker)
    
except KeyboardInterrupt:
    print("Program ended.")      