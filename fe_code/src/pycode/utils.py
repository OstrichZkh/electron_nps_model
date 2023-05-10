import json
import calendar
import datetime
import os
from copy import deepcopy
def fillZero(x,y):
    return 'x' + str(x).zfill(4) + 'y' + str(y).zfill(4)
# 将d8文件转化为上下游关系字典
def d8toDict(d8DF,projectFile):
    # 传输路径hashmap
    transDict = {}
    Y = len(d8DF)
    X = len(d8DF[0])
    for y in range(0,Y):
        for x in range(0,X):
            d8code = d8DF[y][x]
            # x0001y0001
            fromCode = fillZero(x,y)
            if d8code == 1 and x+1<X:
                toCode = fillZero(x+1,y)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 2 and x+1<X and y+1<Y:
                toCode = fillZero(x+1,y+1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 4  and y+1<Y:
                toCode = fillZero(x,y+1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 8  and x-1>=0 and y+1<Y:
                toCode = fillZero(x-1,y+1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 16 and x-1>0:
                toCode = fillZero(x-1,y)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 32 and x-1>0 and y-1>0:
                toCode = fillZero(x-1,y-1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 64 and y-1>0:
                toCode = fillZero(x,y-1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
            elif d8code == 128 and x+1<X and y-1>=0:
                toCode = fillZero(x+1,y-1)
                if toCode in transDict:
                    transDict[toCode].append(fromCode)
                else:
                    transDict[toCode] = [fromCode]
    # python字典保存为json格式
    transDict_json = json.dumps(transDict)
    #将json文件保存为.json格式文件
    with open(projectFile+r'\transDict.json','w+') as file:
        file.write(transDict_json)
    return transDict
# 检查所有空间数据面积是否匹配，不匹配污染进行模拟
def checkAreaMatch(dataframes,names):
    X = len(dataframes[0])
    Y = len(dataframes[0][0])
    for i in range(0,len(dataframes)):
        df = dataframes[0]
        if len(df) != X:
            raise ValueError('{}的dataframe的X值不匹配！'.format(names[i]))
        elif len(df[0]) != Y:
            raise ValueError('{}的dataframe的Y值不匹配！'.format(names[i]))
    #  复制了DEM的DF
    initDF = dataframes[-2]
    for x in range(0,X):
        for y in range(0,Y):
            dem = initDF[x][y]
            if dem > 0 and dem < 8848:
                initDF[x][y] = 0
            else:
                initDF[x][y] = -1
    return [X,Y,initDF]
# 土地利用类型全都以1、2、3的形式表示，获取每个code对应的土地利用类型是什么
def getLanduseCode(projectInfo):
    # [{'type': 'forest', 'code': 1}, {'type': 'paddy', 'code': 2},
    # {'type': 'water', 'code': 3}, {'type': 'sloping', 'code': 4},
    # {'type': 'construct', 'code': 5}]
    code = projectInfo["landUse"]["code"]
    landuseDict = {}
    for c in code :
        landuseDict[c["code"]] = c['type']
    return landuseDict
# 获取用户定义的施肥措施信息
def getManagementInfo(projectInfo):
    # 管理措施字典
    managementDict = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: [],
        8: [],
        9: [],
        10: [],
        11: [],
        12: []
    }
    for measure in projectInfo["measures"]:
        month = measure['applyMonth']
        managementDict[int(month)].append(measure)
    return managementDict
# 获取用户设置的模型运行时间
def getDataRange(projectInfo):
    startY = projectInfo["periods"]["startDate"].split('/')[0]
    startM = projectInfo["periods"]["startDate"].split('/')[1]
    startD = '1'
    endY = projectInfo["periods"]["endDate"].split('/')[0]
    endM = projectInfo["periods"]["endDate"].split('/')[1]
    if startM[0] == '0':
        startM = startM[1]
    if endM[0] == '0':
        endM = endM[1]
    endD = str(calendar.monthrange(int(endY), int(endM))[1])
    startDate = '-'.join([startY, startM, startD]).split('-')
    endDate = '-'.join([endY, endM, endD]).split('-')
    gapMonth = (int(endDate[0]) - int(startDate[0])) * 12 + (int(endDate[1]) - int(startDate[1])) + 1
    startDateTime = datetime.date(int(startDate[0]), int(startDate[1]), int(startDate[2]))
    endDateTime = datetime.date(int(endDate[0]), int(endDate[1]), int(endDate[2]))
    return [
        startDateTime,
        endDateTime
    ]
# 基于日降雨计算月降雨量
def getMonthlyRainfall(filePath,projInfo):

        rainfallPath = filePath + r'\database\rainfall.txt'
        # 获取降雨列表
        rainfallArr = []
        for line in open(rainfallPath):
            rainfallArr.append(line.replace('\n', ''))
        # 此文件用于计算降雨数据
        rainfallArr.pop(0)


        # 2020-1-1

        startDate = projInfo['periods']['startDate'].split('/')
        endDate = projInfo['periods']['endDate'].split('/')
        startDate.append('01')
        endDate.append(calendar.monthrange(int(endDate[0]), int(endDate[1]))[1])

        startDateTime = datetime.date(int(startDate[0]), int(startDate[1]), int(startDate[2]))
        endDateTime = datetime.date(int(endDate[0]), int(endDate[1]), int(endDate[2]))
        gapDays = (endDateTime - startDateTime).days + 1
        gapYears = float((endDateTime - startDateTime).days / 365)

        monthSum = 0
        monthArr = []
        count = 0
        dateArr = []

        while True:
            # 最后一天了
            monthSum += float(rainfallArr[count])
            count = count + 1
            monBefore = startDateTime.month
            startDateTime = startDateTime + datetime.timedelta(days=1)
            monAfter = startDateTime.month
            # 到了下一个月了
            if (monBefore != monAfter or count == len(rainfallArr)):
                if (monthSum >= 0):
                    monthArr.append(monthSum)
                else:
                    monthArr.append(0)
                monthSum = 0
            if (startDateTime == endDateTime):
                if (monthSum >= 0):
                    monthArr.append(monthSum)
                else:
                    monthArr.append(0)
                monthSum = 0
                break

        rainfallArr_R = []
        for rainfall in rainfallArr:
            if float(rainfall) >= 12:
                rainfallArr_R.append(float(rainfall))
            else:
                rainfallArr_R.append(0)
        temp = 0  # 计算a、b因子的临时list
        count = 0

        for rainfall in rainfallArr:
            if float(rainfall) > 12:
                temp += float(rainfall)
                count += 1
        Pd12 = temp / count
        Py12 = temp / gapYears
        b = 0.8363 + 18.177 / Pd12 + 24.455 / Py12
        a = 21.589 * b ** (-7.1891)

        monthSum1 = 0
        monthArr1 = []
        count1 = 0
        dateArr = []
        startDateTime = datetime.date(int(startDate[0]), int(startDate[1]), int(startDate[2]))
        endDateTime = datetime.date(int(endDate[0]), int(endDate[1]), int(endDate[2]))
        gapDays = (endDateTime - startDateTime).days + 1
        gapYears = float((endDateTime - startDateTime).days / 365)
        while True:
            # 最后一天了
            monthSum1 += float(rainfallArr_R[count1])
            count1 = count1 + 1
            monBefore = startDateTime.month
            startDateTime = startDateTime + datetime.timedelta(days=1)
            monAfter = startDateTime.month
            # 到了下一个月了
            if (monBefore != monAfter or count1 == len(rainfallArr_R)):
                if (monthSum1 >= 0):
                    monthArr1.append(monthSum1)
                else:
                    monthArr1.append(0)
                monthSum1 = 0
            if (startDateTime == endDateTime):
                if (monthSum1 >= 0):
                    monthArr1.append(monthSum1)
                else:
                    monthArr1.append(0)
                monthSum1 = 0
                break

        # 发送给主进程降雨数据
        monthList = []
        curY = int(startDate[0])
        curM = int(startDate[1])
        endY = int(endDate[0])
        endM = int(endDate[1])
        while curY < endY or (curY == endY and curM <= endM):
            monthList.append(str(curY) + '/' + str(curM))
            if curM == 12:
                curM = 1
                curY += 1
            else:
                curM += 1
        rainfallList = []
        for i in range(0, len(monthList)):
            rainfallList.append({
                'date': monthList[i],
                'rainfall': monthArr[i],
                "R_factor": monthArr1[i]
            })
        json_str = json.dumps(rainfallList)
        # with open(filePath + r'\database\R_factor.txt', 'w') as json_file:
        #     json_file.write(json_str)
        return rainfallList

def createResultFile(projectFile,monthRainfall):
    if not os.path.exists(projectFile + r'\modelResult'):
        os.makedirs(projectFile + r'\modelResult')
    for i in range(1, monthRainfall + 1):
        if not os.path.exists(projectFile + r'\modelResult\month' + str(i)):
            os.makedirs(projectFile + r'\modelResult\month' + str(i))


