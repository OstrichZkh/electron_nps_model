import json
import calendar
import datetime
import os
import math
import pandas as pd
from copy import deepcopy

def fillZero(x,y):
    return 'x' + str(x).zfill(4) + 'y' + str(y).zfill(4)
# 将d8文件转化为上下游关系字典
def getCelibrateData(projectInfo,projectFile):
    celibratedTarget = []
    celibratedValue = {}
    observeData = projectInfo['observeData']
    for target in observeData:
        obs = observeData[target]
        if obs['checked'] ==  True and obs['imported'] == True:
            celibratedTarget.append(target)
            path = "{}\observeData\{}.txt".format(projectFile, target)
            arr = []
            for line in open(path):
                arr.append(float(line.replace('\n', '')))
            celibratedValue[target] = arr

    return [celibratedTarget,celibratedValue]
def d8toDict(d8DF,projectFile_):
    # 传输路径hashmap
    global transDict,projectFile
    projectFile = projectFile_
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
    global X,Y,initDF
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
    global landuseDict,forestCode,slopelandCode,paddylandCode,waterCode,buildingCode
    code = projectInfo["landUse"]["code"]
    landuseDict = {}
    for c in code :
        landuseDict[c["code"]] = c['type']

    for item in landuseDict.items():
        if item[1] == 'forest':
            forestCode = item[0]
        elif item[1] == 'sloping':
            slopelandCode = item[0]
        elif item[1] == 'paddy':
            paddylandCode = item[0]
        elif item[1] == 'water':
            waterCode = item[0]
        elif item[1] == 'construct':
            buildingCode = item[0]
    return [landuseDict,forestCode,slopelandCode,paddylandCode,waterCode,buildingCode]
# 获取用户定义的施肥措施信息
def getManagementInfo(projectInfo):
    global managementDict
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
    global startDateTime,endDateTime
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
    global rainfallList
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
# 新建运行的文件夹
def createResultFile(projectFile,monthRainfall):
    if not os.path.exists(projectFile + r'\modelResult'):
        os.makedirs(projectFile + r'\modelResult')
    for i in range(1, monthRainfall + 1):
        if not os.path.exists(projectFile + r'\modelResult\month' + str(i)):
            os.makedirs(projectFile + r'\modelResult\month' + str(i))
# 水文模块
def hydroModule(rainfall,paraDict_,landuseDF_):
    global paraDict,landuseDF,runoff_generate,runoff_soil_generate,runoff_flow,runoff_soil_flow
    paraDict = paraDict_
    landuseDF = landuseDF_
    runoff_generate = deepcopy(initDF)
    runoff_soil_generate = deepcopy(initDF)

    for y in range(0,X):
        for x in range(0,Y):
            if runoff_generate[y][x] == 0:
                # 计算地表产流
                CN = 70
                if landuseDF[y][x] == float(forestCode):
                    CN = paraDict['CN_forest']
                elif landuseDF[y][x] == float(slopelandCode):
                    CN = paraDict['CN_sloping']
                elif landuseDF[y][x] == float(paddylandCode):
                    CN = paraDict['CN_paddy']
                S = 25.4*(1000/CN-10)

                Q_surf = (rainfall- 0.2 * S) ** 2 / (rainfall + 0.8 * S)  # 2-3
                if rainfall < paraDict['R0']:
                #  小于R0，全为壤中流
                    runoff_generate[y][x] = 0
                    runoff_soil_generate[y][x] = Q_surf
                elif rainfall < paraDict['R1']:
                    surface = paraDict['Q_SURF_K1']*(rainfall-paraDict['R0'])
                    soil = paraDict['Q_SOIL_K1']*rainfall
                    runoff_generate[y][x] = Q_surf * surface / (surface + soil)
                    runoff_soil_generate[y][x] = Q_surf * soil / (surface + soil)

                else:
                    surface = paraDict['Q_SURF_K1'] * (paraDict['R1'] - paraDict['R0']) + paraDict['Q_SURF_K2'] * (rainfall - paraDict['R1'])
                    soil = paraDict['Q_SOIL_K1'] * paraDict['R1']
                    runoff_generate[y][x] = Q_surf * surface / (surface + soil)
                    runoff_soil_generate[y][x] = Q_surf * soil / (surface + soil)
    # 地表径流、壤中流汇流
    runoff_flow = deepcopy(runoff_generate)
    runoff_soil_flow = deepcopy(runoff_soil_generate)
    # 水文汇流过程，无拦截损失
    def confluence(x,y):
        xyCode = fillZero(x,y)
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                [preRunoff,preSoil] = confluence(preX,preY)
                runoff_flow[y][x] += preRunoff
                runoff_soil_flow[y][x] += preSoil
            return [runoff_flow[y][x],runoff_soil_flow[y][x]]
        else:
            return [runoff_flow[y][x],runoff_soil_flow[y][x]]
    # 汇流过程
    confluence(44,209)
    return [
        runoff_generate,
        runoff_soil_generate,
        runoff_flow,
        runoff_soil_flow
    ]
def soilProcess(month,preMonthResult):
    global minP_act,minP_sta,orgP_hum ,orgP_frsh ,orgP_act ,orgP_sta ,P_solution ,NO3 ,orgN_hum ,orgN_act , orgN_sta ,orgN_frsh
    t_soil = 20
    y_tmp_ly = 0.9 * (t_soil) / (t_soil + math.exp(9.93 - 0.312 * t_soil)) + 0.1  # 3-7
    _trans = paraDict['SOL_BD'] * 10 / 100  # 3-47
    sw_ave = 0.5
    FC_ly = 0.4 * paraDict['CLAY'] * paraDict['SOL_BD'] / 100 + paraDict['SOL_AWC']  # 2-103
    if month == 1:
    # 第一个月，初始化P
        minP_act= deepcopy(initDF)
        minP_sta = deepcopy(initDF)
        orgP_hum = deepcopy(initDF)
        orgP_frsh = deepcopy(initDF)
        orgP_act = deepcopy(initDF)
        orgP_sta = deepcopy(initDF)
        P_solution = deepcopy(initDF)
        NO3 = deepcopy(initDF)
        orgN_hum = deepcopy(initDF)
        orgN_act = deepcopy(initDF)
        orgN_sta = deepcopy(initDF)
        orgN_frsh = deepcopy(initDF)
        # 初始化部分库
        for y in range(0,X):
            for x in range(0,Y):
                if initDF[y][x] !=0 or landuseDF[y][x] == waterCode or landuseDF[y][x] == buildingCode:
                    continue
                else:
                    # 初始化，单位均为kg/hm2
                    if (landuseDF[y][x] == paddylandCode or landuseDF[y][x] == slopelandCode):
                        P_solution[y][x] = 25 * _trans
                    else:
                        P_solution[y][x] = 5 * _trans
                    minP_act[y][x] =  P_solution[y][x] * (1 - paraDict['PSP']) / paraDict['PSP']  # 3-43
                    minP_sta[y][x] = 4 * minP_act[y][x]  # 3-44
                    orgP_hum[y][x] = 0.125 * 10000 * paraDict['SOL_CBN'] / 14 * _trans
                    orgP_frsh[y][x] = 0.0003 * paraDict['RSDIN']  # paraDict['RSDIN'] : 0-10000
                    orgN_hum[y][x] = 10000 * paraDict['SOL_CBN'] / 14 * _trans  # paraDict['SOL_CBN'] : 0.05-10
                    orgN_act[y][x] = orgN_hum[y][x] * 0.02
                    orgN_sta[y][x] = orgN_hum[y][x] * 0.98
                    orgN_frsh[y][x] = 0.0015 * paraDict['RSDIN']
                    # print(
                    #       minP_act[y][x] ,
                    #       minP_sta[y][x] ,
                    #       orgP_hum[y][x] ,
                    #       orgP_frsh[y][x],
                    #       orgN_hum[y][x] ,
                    #       orgN_act[y][x] ,
                    #       orgN_sta[y][x] ,
                    #       orgN_frsh[y][x],
                    #       )
                    #     硝态氮初始化
                    NO3[y][x] = 7 * math.exp(-10 / 1000) * _trans
                    #     营养物循环温度、水因子
                    y_sw_ly = sw_ave / FC_ly  # 3-8
                    #   （一）、腐殖质的矿化过程 P110
                    N_trans_ly = paraDict['CMN'] * orgN_act[y][x] * (1 / 0.02 - 1) - orgN_sta[y][x]  # 3-9
                    orgN_act[y][x] -= N_trans_ly
                    orgN_sta[y][x] += N_trans_ly
                    if orgN_act[y][x] < 0 :
                        orgN_act[y][x] = 0
                    if  orgN_sta[y][x] < 0:
                        orgN_sta[y][x] = 0
                    N_min_ly = paraDict['CMN'] * math.sqrt(y_tmp_ly * y_sw_ly) * orgN_act[y][x]  # 3-10
                    # print('N_min_ly:',N_min_ly)   0.058
                    NO3[y][x] += N_min_ly
                    orgN_act[y][x] -= N_min_ly
                    #   （二）、残留物的分解作用和矿化作用 P110
                    C_N_ratio = 0.58 * paraDict['RSDIN'] / (orgN_frsh[y][x] + NO3[y][x])  # 3-11
                    C_P_ratio = 0.58 * paraDict['RSDIN'] / (orgP_frsh[y][x] + P_solution[y][x])  # 3-12
                    y_ntr_ly = min(math.exp(-0.693 * (C_N_ratio - 25) / 25),
                                   math.exp(-0.693 * (C_P_ratio - 200) / 200), 1)  # 3-14
                    delta_ntr_ly = paraDict['RSDCO'] * y_ntr_ly * math.sqrt(y_tmp_ly * y_sw_ly)  # 3-13
                    N_min_frsh_ly = 0.8 * delta_ntr_ly * orgN_frsh[y][x]  # 新生有机氮库矿化的氮量 3-15
                    N_dee_ly = 0.2 * delta_ntr_ly * orgN_frsh[y][x]  # 新生有机氮库分解的氮量 3-16
                    NO3[y][x] += N_min_frsh_ly  # 进入硝酸盐库
                    orgN_act[y][x] += N_dee_ly  # 进入活性有机氮库
                    orgN_frsh[y][x] -= N_dee_ly + N_min_frsh_ly  # 分解的新生氮
                    orgN_hum[y][x] = orgN_act[y][x] + orgN_sta[y][x]  # 腐殖质的有机氮=活性+稳定
                    #   （三）、磷的矿化作用
                    orgP_act[y][x] = orgP_hum[y][x] * orgN_act[y][x] / (orgN_act[y][x] + orgN_sta[y][x])  # 3-50
                    orgP_sta[y][x] = orgP_hum[y][x] * orgN_sta[y][x] / (orgN_act[y][x] + orgN_sta[y][x])  # 3-51
                    p_mina_ly = 1.4 * paraDict['RSDCO'] * math.sqrt(y_tmp_ly * y_sw_ly) * orgP_act[y][x]  # 3-52 从活性有机磷矿化到溶解磷
                    if p_mina_ly > orgP_sta[y][x]:
                        p_mina_ly = 0.9 * orgP_sta[y][x]
                    orgP_sta[y][x] -= p_mina_ly
                    P_solution[y][x] += p_mina_ly
                    #    （四）、残留物的分解作用及矿化作用
                    P_min_frsh_ly = 0.8 * delta_ntr_ly * orgP_frsh[y][x]  # 新生有机氮库矿化的磷量 3-57
                    P_dee_ly = 0.2 * delta_ntr_ly * orgP_frsh[y][x]  # 新生有机氮库分解的磷量 3-58
                    if P_min_frsh_ly >  orgP_frsh[y][x]:
                        P_min_frsh_ly = 0.9 *  orgP_frsh[y][x]
                    if P_dee_ly > orgP_frsh[y][x]:
                        P_dee_ly = 0.9 * orgP_frsh[y][x]
                    orgP_frsh[y][x] -= P_min_frsh_ly
                    P_solution[y][x] += P_min_frsh_ly
                    orgP_frsh[y][x] -= P_dee_ly
                    orgP_hum[y][x] += P_dee_ly
                    #   （五）、无机磷的吸附作用
                    if P_solution[y][x] > minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']):
                        P_sol_act_ly = 0.1 * (
                                P_solution[y][x] - minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']))  # 3-60
                    else:
                        P_sol_act_ly = 0.6 * (
                                P_solution[y][x] - minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']))  # 3-60
                    if P_sol_act_ly >  P_solution[y][x]:
                        P_sol_act_ly = 0.9 * P_solution[y][x]
                    minP_act[y][x] += P_sol_act_ly
                    P_solution[y][x] -= P_sol_act_ly
                    if minP_sta[y][x] < 4 * minP_act[y][x]:
                        P_act_sta_ly = 31 * 0.0006 * (4 * minP_act[y][x] - minP_sta[y][x])  # 3-62
                    else:
                        P_act_sta_ly = 0.1 * 31 * 0.0006 * (4 * minP_act[y][x] - minP_sta[y][x])  # 3-63
                    if P_act_sta_ly > minP_act[y][x]:
                        P_act_sta_ly = 0.9 * minP_act[y][x]
                    minP_act[y][x] -= P_act_sta_ly
                    minP_sta[y][x] += P_act_sta_ly
    else:
        #不是第一个月，要看施肥情况了
        # 获取上个月的土壤磷结果
        minP_act = preMonthResult['minP_act']
        minP_sta = preMonthResult['minP_sta']
        orgP_hum = preMonthResult['orgP_hum']
        orgP_frsh = preMonthResult['orgP_frsh']
        orgP_act = preMonthResult['orgP_act']
        orgP_sta = preMonthResult['orgP_sta']
        P_solution = preMonthResult['P_solution']
        NO3 = preMonthResult['NO3']
        orgN_hum = preMonthResult['orgN_hum']
        orgN_act = preMonthResult['orgN_act']
        orgN_sta = preMonthResult['orgN_sta']
        orgN_frsh = preMonthResult['orgN_frsh']
        #获取农业数据
        mon = (month % 12)
        if mon == 0 :
            mon = 12
        # print(month,mon,managementDict)
        monManagementList = managementDict[mon]
        # 本月N、P的外源输入量
        N_input = 0
        P_input = 0
        for management in monManagementList:
            N_input += float(management['amount'])*float(management['N_ration'])
            P_input += float(management['amount'])*float(management['P_ration'])
        NO3_fert_slope = paraDict['FMINN'] * (1 - paraDict['FNH3N']) * N_input
        NH4_fert_slope = paraDict['FMINN'] * (1 - paraDict['FNH3N']) * N_input
        orgN_frsh_slope = 0.5 * paraDict['FORGN'] * N_input
        orgN_act_slope = 0.5 * paraDict['FORGN'] * N_input
        P_solution_slope = paraDict['FMINP'] * P_input
        orgP_frsh_slope = 0.5 * paraDict['FORGP'] * P_input
        orgP_hum_slope =  0.5 * paraDict['FORGP'] *P_input
        # 本月变化
        for y in range(0,X):
            for x in range(0,Y):
                if landuseDF[y][x] == waterCode or landuseDF[y][x] == buildingCode:
                    continue
                else:
                    # 化肥添加
                    if landuseDF[y][x] == slopelandCode or landuseDF[y][x] == paddylandCode:
                        NO3[y][x] += NO3_fert_slope
                        orgN_frsh[y][x] += orgN_frsh_slope
                        orgN_act[y][x] += orgN_act_slope
                        P_solution[y][x] += P_solution_slope
                        orgP_frsh[y][x] += orgP_frsh_slope
                        orgP_hum[y][x] += orgP_hum_slope
                    #     营养物循环温度、水因子
                    y_sw_ly = sw_ave / FC_ly  # 3-8
                    #   （一）、腐殖质的矿化过程 P110
                    N_trans_ly = paraDict['CMN'] * orgN_act[y][x] * (1 / 0.02 - 1) - orgN_sta[y][x]  # 3-9
                    orgN_act[y][x] -= N_trans_ly
                    orgN_sta[y][x] += N_trans_ly
                    if orgN_act[y][x] < 0 :
                        orgN_act[y][x] = 0
                    if  orgN_sta[y][x] < 0:
                        orgN_sta[y][x] = 0
                    N_min_ly = paraDict['CMN'] * math.sqrt(y_tmp_ly * y_sw_ly) * orgN_act[y][x]  # 3-10
                    # print('N_min_ly:',N_min_ly)   0.058
                    NO3[y][x] += N_min_ly
                    orgN_act[y][x] -= N_min_ly
                    #   （二）、残留物的分解作用和矿化作用 P110
                    if orgN_frsh[y][x] + NO3[y][x] == 0:
                        C_N_ratio = 0.5
                    else:
                        C_N_ratio = 0.58 * paraDict['RSDIN'] / (orgN_frsh[y][x] + NO3[y][x])  # 3-11
                    if orgP_frsh[y][x] + P_solution[y][x] == 0:
                        C_P_ratio = 0.5
                    else:
                        C_P_ratio = 0.58 * paraDict['RSDIN'] / (orgP_frsh[y][x] + P_solution[y][x])  # 3-12
                    y_ntr_ly = min(math.exp(-0.693 * (C_N_ratio - 25) / 25),
                                       math.exp(-0.693 * (C_P_ratio - 200) / 200), 1)  # 3-14
                    delta_ntr_ly = paraDict['RSDCO'] * y_ntr_ly * math.sqrt(y_tmp_ly * y_sw_ly)  # 3-13
                    N_min_frsh_ly = 0.8 * delta_ntr_ly * orgN_frsh[y][x]  # 新生有机氮库矿化的氮量 3-15
                    N_dee_ly = 0.2 * delta_ntr_ly * orgN_frsh[y][x]  # 新生有机氮库分解的氮量 3-16
                    NO3[y][x] += N_min_frsh_ly  # 进入硝酸盐库
                    orgN_act[y][x] += N_dee_ly  # 进入活性有机氮库
                    orgN_frsh[y][x] -= N_dee_ly + N_min_frsh_ly  # 分解的新生氮
                    orgN_hum[y][x] = orgN_act[y][x] + orgN_sta[y][x]  # 腐殖质的有机氮=活性+稳定
                    #   （三）、磷的矿化作用
                    if orgN_act[y][x] + orgN_sta[y][x] == 0:
                        orgP_act[y][x] = orgP_hum[y][x] * 0.5
                        orgP_sta[y][x] = orgP_hum[y][x] * 0.5
                    else:
                        orgP_act[y][x] = orgP_hum[y][x] * orgN_act[y][x] / (orgN_act[y][x] + orgN_sta[y][x])  # 3-50
                        orgP_sta[y][x] = orgP_hum[y][x] * orgN_sta[y][x] / (orgN_act[y][x] + orgN_sta[y][x])  # 3-51
                    p_mina_ly = 1.4 * paraDict['RSDCO'] * math.sqrt(y_tmp_ly * y_sw_ly) * orgP_act[y][
                        x]  # 3-52 从活性有机磷矿化到溶解磷
                    if p_mina_ly > orgP_sta[y][x]:
                        p_mina_ly = 0.9 * orgP_sta[y][x]
                    orgP_sta[y][x] -= p_mina_ly
                    P_solution[y][x] += p_mina_ly
                    #    （四）、残留物的分解作用及矿化作用
                    P_min_frsh_ly = 0.8 * delta_ntr_ly * orgP_frsh[y][x]  # 新生有机氮库矿化的磷量 3-57
                    P_dee_ly = 0.2 * delta_ntr_ly * orgP_frsh[y][x]  # 新生有机氮库分解的磷量 3-58
                    if P_min_frsh_ly >  orgP_frsh[y][x]:
                        P_min_frsh_ly = 0.9 *  orgP_frsh[y][x]
                    if P_dee_ly > orgP_frsh[y][x]:
                        P_dee_ly = 0.9 * orgP_frsh[y][x]
                    orgP_frsh[y][x] -= P_min_frsh_ly
                    P_solution[y][x] += P_min_frsh_ly
                    orgP_frsh[y][x] -= P_dee_ly
                    orgP_hum[y][x] += P_dee_ly
                    #   （五）、无机磷的吸附作用
                    if P_solution[y][x] > minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']):
                        P_sol_act_ly = 0.1 * (
                                P_solution[y][x] - minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']))  # 3-60
                    else:
                        P_sol_act_ly = 0.6 * (
                                P_solution[y][x] - minP_act[y][x] * paraDict['PSP'] / (1 - paraDict['PSP']))  # 3-60
                    if P_sol_act_ly >  P_solution[y][x]:
                        P_sol_act_ly = 0.9 * P_solution[y][x]
                    minP_act[y][x] += P_sol_act_ly
                    P_solution[y][x] -= P_sol_act_ly
                    if minP_sta[y][x] < 4 * minP_act[y][x]:
                        P_act_sta_ly = 31 * 0.0006 * (4 * minP_act[y][x] - minP_sta[y][x])  # 3-62
                    else:
                        P_act_sta_ly = 0.1 * 31 * 0.0006 * (4 * minP_act[y][x] - minP_sta[y][x])  # 3-63
                    if P_act_sta_ly > minP_act[y][x]:
                        P_act_sta_ly = 0.9 * minP_act[y][x]
                    minP_act[y][x] -= P_act_sta_ly
                    minP_sta[y][x] += P_act_sta_ly

    return [
        minP_act,
        minP_sta ,
        orgP_hum ,
        orgP_frsh ,
        orgP_act ,
        orgP_sta ,
        P_solution ,
        NO3 ,
        orgN_hum ,
        orgN_act ,
        orgN_sta ,
        orgN_frsh ,
    ]

def colProcess(phDict,rusle):
    global colSource_surface,colSource_soil
    # 地表、壤中流、地下水胶体模拟
    colSource_surface = deepcopy(initDF)
    colSource_soil = deepcopy(initDF)

    slopeColPara = 1.55 * (paraDict["PARA_PH0"] +
                           paraDict["PARA_PH1"] * phDict['坡耕地'] +
                           paraDict["PARA_PH2"] * (phDict['坡耕地']**2) +
                           paraDict["PARA_PH3"] * (phDict['坡耕地'] ** 3) +
                           paraDict["PARA_PH4"] * (phDict['坡耕地'] ** 4)
                           )
    paddyColPara = 5.27 *(paraDict["PARA_PH0"] +
                           paraDict["PARA_PH1"] * phDict['水田'] +
                           paraDict["PARA_PH2"] * (phDict['水田']**2) +
                           paraDict["PARA_PH3"] * (phDict['水田'] ** 3) +
                           paraDict["PARA_PH4"] * (phDict['水田'] ** 4)
                           )

    forestColPara = 0.46 *(paraDict["PARA_PH0"] +
                           paraDict["PARA_PH1"] * phDict['林地'] +
                           paraDict["PARA_PH2"] * (phDict['林地']**2) +
                           paraDict["PARA_PH3"] * (phDict['林地'] ** 3) +
                           paraDict["PARA_PH4"] * (phDict['林地'] ** 4)
                           )
    if (forestColPara < 0 or forestColPara > 10) or (paddyColPara < 0 or paddyColPara > 10) or (slopeColPara < 0 or slopeColPara > 10):
        forestColPara = 0.46 * paraDict['defaultCol']
        paddyColPara  = 5.27 * paraDict['defaultCol']
        slopeColPara  = 1.55 * paraDict['defaultCol']


    for y in range(0, X):
        for x in range(0, Y):
            runoff = runoff_generate[y][x]
            soil = runoff_soil_generate[y][x]
            if runoff + soil == 0:
                runoff_ratio = 0
                soil_ratio = 0
            else:
                runoff_ratio = runoff / (runoff + soil)
                soil_ratio = soil / (runoff + soil)
            source = 0
            if landuseDF[y][x] == float(forestCode):
                source = forestColPara * rusle[y][x]
            elif landuseDF[y][x] == float(slopelandCode):
                source = slopeColPara * rusle[y][x]
            elif landuseDF[y][x] == float(paddylandCode):
                source = paddyColPara * rusle[y][x]
            colSource_soil[y][x] = source * soil_ratio
            colSource_surface[y][x] = source * runoff_ratio
    return [
        colSource_surface,
        colSource_soil
    ]

def pollutionSourceProcess(rusle):
    global solPSource_soil,solPSource_surface,sedPSource_soil,sedPSource_surface,colPSource_soil,colPSource_surface
    solPSource_surface = deepcopy(initDF)
    solPSource_soil = deepcopy(initDF)

    sedPSource_surface = deepcopy(initDF)
    sedPSource_soil = deepcopy(initDF)

    colPSource_surface = deepcopy(initDF)
    colPSource_soil = deepcopy(initDF)

    for y in range(0, X):
        for x in range(0, Y):
            runoff = runoff_generate[y][x]
            soil = runoff_soil_generate[y][x]
            if runoff + soil == 0:
                runoff_ratio = 0
                soil_ratio = 0
            else:
                runoff_ratio = runoff / (runoff + soil)
                soil_ratio = soil / (runoff + soil)
            if initDF[y][x] != 0 or landuseDF[y][x] == waterCode or landuseDF[y][x] == buildingCode or runoff_flow[y][
                x] == 0 or rusle[y][x] == 0:
                continue
            else:
                conc_sedP = 100 * (minP_act[y][x] + minP_sta[y][x] + orgP_hum[y][x] + orgP_frsh[y][x]) / (
                        paraDict['SOL_BD'] * 10)
                conc_sedSurf = rusle[y][x] / (10 * 0.09 * runoff_flow[y][x])
                EPsed = 0.78 * conc_sedSurf ** (-0.2468)
                solPSource = P_solution[y][x] * runoff_flow[y][x] * 0.09 / (paraDict['SOL_BD'] * 10 * 0.5)
                sedPSource = 0.0001 * rusle[y][x] * conc_sedP * EPsed
                colPSource = 0.0001 * (colSource_surface[y][x] + colSource_soil[y][x]) * conc_sedP * EPsed

                solPSource_soil[y][x] = solPSource * soil_ratio
                solPSource_surface[y][x] = solPSource * runoff_ratio

                sedPSource_soil[y][x] = sedPSource * soil_ratio
                sedPSource_surface[y][x] = sedPSource * runoff_ratio

                colPSource_soil[y][x] = colPSource * soil_ratio
                colPSource_surface[y][x] = colPSource * runoff_ratio
    return [
        solPSource_soil,
        solPSource_surface,
        sedPSource_soil,
        sedPSource_surface,
        colPSource_soil,
        colPSource_surface
    ]

def pollutionTranslateProcess(slopeDF,C_factorDF):


    # 污染汇
    solPFlow_surface = deepcopy(solPSource_surface)
    colPFlow_surface = deepcopy(colPSource_surface)
    sedPFlow_surface = deepcopy(sedPSource_surface)
    # colFlow_surface = copy.deepcopy(colPSource_surface)
    # sedFlow = copy.deepcopy(rusle)
    solPFlow_soil = deepcopy(solPSource_soil)
    colPFlow_soil = deepcopy(colPSource_soil)
    sedPFlow_soil = deepcopy(sedPSource_soil)
    # colFlow_soil = copy.deepcopy(colPSource_soil)

    def flow(x,y):
        runoff = runoff_generate[y][x]
        soil = runoff_soil_generate[y][x]
        if runoff + soil == 0:
            runoff_ratio = 0
            soil_ratio = 0
        else:
            runoff_ratio = runoff / (runoff + soil)
            soil_ratio = soil / (runoff + soil)
        xyCode = fillZero(x, y)
        if not slopeDF[y][x] > 0:
            slopeDF[y][x] = 0.01
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                preRes = flow(preX,preY)
                solPFlow_surface[y][x] += preRes['solPFlow_surface']
                colPFlow_surface[y][x] += preRes['colPFlow_surface']
                sedPFlow_surface[y][x] += preRes['sedPFlow_surface']
                # colFlow_surface[y][x] += preRes['colFlow_surface']
                # sedFlow[y][x] += preRes['sedFlow']
                solPFlow_soil[y][x] += preRes['solPFlow_soil']
                colPFlow_soil[y][x] += preRes['colPFlow_soil']
                sedPFlow_soil[y][x] += preRes['sedPFlow_soil']
                # colFlow_soil[y][x] += preRes['colFlow_soil']
                if runoff_flow[y][x] == 0:
                    solP_loss = 1
                    colP_loss = 1
                    sedP_loss = 1
                else:
                    solP_loss = paraDict['INTER_RESP_PARA_1'] * (C_factorDF[y][x] / 10000) + \
                                              paraDict['INTER_RESP_PARA_2'] * (runoff_flow[y][x] ** paraDict['INTER_RESP_PARA_3']) + \
                                               paraDict['INTER_RESP_PARA_4'] * (solPSource_surface[y][x]) + \
                                              paraDict['INTER_RESP_PARA_5'] * (slopeDF[y][x])
                    colP_loss = paraDict['INTER_COLP_PARA_1'] * (-C_factorDF[y][x] / 10000) + \
                                              paraDict['INTER_COLP_PARA_2'] * (
                                                          runoff_flow[y][x] ** paraDict['INTER_COLP_PARA_3']) + \
                                              paraDict['INTER_COLP_PARA_4'] * (colPSource_surface[y][x]) + \
                                              paraDict['INTER_COLP_PARA_5'] * (slopeDF[y][x])
                    sedP_loss = paraDict['INTER_SEDP_PARA_1'] * (-C_factorDF[y][x] / 10000) + \
                                              paraDict['INTER_SEDP_PARA_2'] * (
                                                      runoff_flow[y][x] ** paraDict['INTER_SEDP_PARA_3']) + \
                                              paraDict['INTER_SEDP_PARA_4'] * (sedPSource_surface[y][x]) + \
                                              paraDict['INTER_SEDP_PARA_5'] * (slopeDF[y][x])
                try:
                    solPFlow_surface[y][x] = solP_loss * runoff_ratio
                    colPFlow_surface[y][x] = colP_loss * runoff_ratio
                    sedPFlow_surface[y][x] = sedP_loss * runoff_ratio
                    solPFlow_soil[y][x] = solP_loss * soil_ratio
                    colPFlow_soil[y][x] = colP_loss * soil_ratio
                    sedPFlow_soil[y][x] = sedP_loss * soil_ratio
                except:
                    solPFlow_surface[y][x] = 0
                    colPFlow_surface[y][x] = 0
                    sedPFlow_surface[y][x] = 0
                    solPFlow_soil[y][x] = 0
                    colPFlow_soil[y][x] = 0
                    sedPFlow_soil[y][x] = 0


            return {
                'solPFlow_surface': solPFlow_surface[y][x],
                'colPFlow_surface': colPFlow_surface[y][x],
                'sedPFlow_surface': sedPFlow_surface[y][x],
                # 'colFlow_surface': colFlow_surface[y][x],
                # 'sedFlow': sedFlow[y][x],
                'solPFlow_soil': solPFlow_soil[y][x],
                'colPFlow_soil': colPFlow_soil[y][x],
                'sedPFlow_soil': sedPFlow_soil[y][x],
                # 'colFlow_soil': colFlow_soil[y][x],
            }
        else:
            return {
                'solPFlow_surface':solPFlow_surface[y][x],
                'colPFlow_surface':colPFlow_surface[y][x],
                'sedPFlow_surface':sedPFlow_surface[y][x],
                # 'colFlow_surface':colFlow_surface[y][x],
                # 'sedFlow':sedFlow[y][x],
                'solPFlow_soil':solPFlow_soil[y][x],
                'colPFlow_soil':colPFlow_soil[y][x],
                'sedPFlow_soil':sedPFlow_soil[y][x],
                # 'colFlow_soil':colFlow_soil[y][x],
            }
    flow(44,209)

    return [
        solPFlow_surface,
        colPFlow_surface,
        sedPFlow_surface,
        solPFlow_soil,
        colPFlow_soil,
        sedPFlow_soil,
    ]