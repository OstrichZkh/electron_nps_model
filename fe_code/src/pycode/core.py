import sys
import pandas as pd
import json
import numpy as np
import datetime
import os
import copy
import math
import time
import utils
# 外部传入参数 项目地址、项目json信息
# projectFile = sys.argv[1]


projectFile = r'E:\webplatform\asd'
fileList = os.listdir(projectFile+r'\observeData')
# 获取率定目标及观测值
celibratedTarget = []
celibratedValue = {}
for file in fileList:
    key = file.split('.')[0]
    #
    celibratedTarget.append(key)
    path = "{}\observeData\{}".format(projectFile,file)
    arr = []
    for line in open(path):
        arr.append(float(line.replace('\n', '')))
    celibratedValue[key] = arr
# mock
celibratedTarget = ['sedP','solP']
celibratedValue = {
    'sedP':[0.0275,0.0305,0.047,0.068,0.036,0.045],
    'solP': [0.024, 0.0305, 0.018, 0.033, 0.0305, 0.028],
    # 'col':[0.0105,0.0125,0.225,0.162,0.144]
}
# 读取地理数据
landuseDF = pd.read_csv(projectFile+r'\database\landuse.csv',index_col=0).values
d8DF = pd.read_csv(projectFile + r'\database\D8.csv',index_col=0).values
C_factorDF = pd.read_csv(projectFile + r'\database\C_factor.csv',index_col=0).values
K_factorDF = pd.read_csv(projectFile + r'\database\K_factor_10000times.csv',index_col=0).values
L_factorDF = pd.read_csv(projectFile + r'\database\L_factor.csv',index_col=0).values
S_factorDF = pd.read_csv(projectFile + r'\database\S_factor.csv',index_col=0).values
demDF = pd.read_csv(projectFile+r'\database\DEM.csv',index_col=0).values
slopeDF = pd.read_csv(projectFile+r'\database\slope.csv',index_col=0).values
[X,Y] = utils.checkAreaMatch(
    [landuseDF,d8DF,C_factorDF,K_factorDF,L_factorDF,S_factorDF,demDF,slopeDF],
    ["土地利用类型","D8","C因子","K因子","L因子","S因子","DEM","坡度"],
)
# 获取时间跨度
dateRange = []
with open(projectFile+r'\database\R_factor.txt', "r", encoding="utf-8") as f:
    dateRange = json.load(f)
phDict = {
    '坡耕地':6,
    '林地':6.5,
    '水田':6
}
def fillZero(x,y):
    return 'x' + str(x).zfill(4) + 'y' + str(y).zfill(4)
# 计算上下游关系字典
transDict = utils.d8toDict(d8DF,projectFile)


# 计算DEM的最大、最小值，地下水模块可能有用
minDEM = 65535
maxDEM = 0
for y in range(0, Y):
    for x in range(0, X):
        if demDF[x][y] > 0 and demDF[x][y] < 8848:
            if demDF[x][y]<minDEM:
                minDEM =demDF[x][y]
            if demDF[x][y] > maxDEM:
                maxDEM = demDF[x][y]

# 赋予code值
with open(projectFile+'\landuseCode.json','r',encoding='utf-8') as fp:
    landuseDict = json.load(fp)

landuseDictDemo = {'1': '林地',
 '2': '坡耕地',
 '3': '河道',
 '4': '水田',
 '5': '建设用地'}
for item in landuseDict.items():
    if item[1]=='林地':
        forestCode = item[0]
    elif item[1]=='坡耕地':
        slopelandCode = item[0]
    elif item[1]=='水田':
        paddylandCode = item[0]
    elif item[1] == '河道' or item[1] == '池塘':
        waterCode = item[0]
    elif item[1] == '建设用地':
        buildingCode = item[0]
# 施肥措施数据
with open(projectFile+'\management.json','r',encoding='utf-8') as fp:
    managementList = json.load(fp)
# 管理措施字典
managementDict = {
    1:[],
    2:[],
    3:[],
    4:[],
    5:[],
    6:[],
    7:[],
    8:[],
    9:[],
    10:[],
    11:[],
    12:[]
}
# eg.
# mgt = {
#     'name': '六月施肥',
#     'description': '复合',
#     'fertAmt': '300',
#     'fertMonth': 6,
#     'fertNtrPer': '0.4',
#     'fertPhoPer': '0.6',
#     'index': 1663500575621
# }
for management in managementList:
    managementDict[management['fertMonth']].append(management)
# 日期数据
with open(projectFile+'\dataInfo.json','r',encoding='utf8') as fp:
    dataInfo = json.load(fp)
startDate = dataInfo['periods']['startDate'].split('-')
endDate = dataInfo['periods']['endDate'].split('-')
gapMonth = (int(endDate[0])-int(startDate[0]))*12 +(int(endDate[1])-int(startDate[1]))+ 1
startDateTime = datetime.date(int(startDate[0]),int(startDate[1]),int(startDate[2]))
endDateTime = datetime.date(int(endDate[0]),int(endDate[1]),int(endDate[2]))
# 初始csv，0 and 65535
initDF = pd.read_csv(projectFile+r'\init0.csv',index_col=0).values.tolist()
X = len(initDF[0]) # 92
Y = len(initDF) # 211
# 获得每月的降雨总量
monthArr = []
R_factor = []
for line in open(projectFile +r'\rain.txt'):
    R_factor.append(line.replace('\n',''))
R_factor.pop(0)
monthSum = 0
count = 0
while True:
    # 最后一天了
    if(startDateTime>endDateTime):
        break
    monthSum += float(R_factor[count])
    count = count + 1
    monBefore = startDateTime.month
    startDateTime = startDateTime+datetime.timedelta(days=1)
    monAfter = startDateTime.month
    # 到了下一个月了
    if(monBefore!=monAfter or count==len(R_factor)):
        if(monthSum>=0):
            monthArr.append(monthSum)
        else:
            monthArr.append(0)
        monthSum = 0
# 每月的降雨总量
monthRainfall = monthArr
# 创建空文件夹
if not os.path.exists(projectFile+r'\modelResult'):
    os.makedirs(projectFile+r'\modelResult')
for i in range(1,8):
    if not os.path.exists(projectFile+r'\modelResult\month'+str(i)):
        os.makedirs(projectFile+r'\modelResult\month'+str(i))

# 开始汇流计算
def oneMonthProcess(paraDict,month,preMonthResult):
    # 读取rusle数据
    rusle = pd.read_csv(r'C:\Users\yezouhua\Desktop\master\webPlatform\数据\RUSLE数据\RUSLE'+str(i)+'.csv',index_col=0).values
    # 基于D8计算每个月的降雨产流，生成runoff.csv文件
    runoff_generate = copy.deepcopy(initDF)
    # 壤中流产流
    runoff_soil_generate = copy.deepcopy(initDF)
    # 浅层地下水产流
    runoff_groundwater_generate = copy.deepcopy(initDF)
    # min = 9999
    # max = 0
    # for y in range(0, Y):
    #     for x in range(0, X):
    #         if slope[y][x]/100+P[y][x] > max:
    #             max = slope[y][x]/100+P[y][x]
    #         if slope[y][x]/100+P[y][x] < min:
    #             min = slope[y][x]/100+P[y][x]
    # print(min,max)
    for y in range(0,Y):
        for x in range(0,X):
            if runoff_generate[y][x] == 0:
                # 计算地表产流
                CN = paraDict['CN1']
                if landuseDF[y][x] == float(forestCode):
                    CN = paraDict['CN1']
                elif landuseDF[y][x] == float(slopelandCode):
                    CN = paraDict['CN2']
                elif landuseDF[y][x] == float(paddylandCode):
                    CN = paraDict['CN2']
                S = 25.4*(1000/CN-10)
                Q_surf = (monthRainfall[month - 1] - 0.2 * S) ** 2 / (monthRainfall[month - 1] + 0.8 * S)  # 2-3

                if False and Q_surf <= paraDict['rzl_threshold']:
                    # 产生径流小于一定的阈值时，全部为壤中流
                    runoff_generate[y][x] = 0
                    runoff_soil_generate[y][x] = Q_surf
                    runoff_groundwater_generate[y][x] = 0
                else:
                    # 否则，按照比例进行下渗
                    # surfaceToSoil = 1-math.exp(paraDict['rzlRation']*(1-runoff_generate[y][x]))
                    surfaceToSoil = (slope[y][x]/100+P[y][x])/2
                    soilToUnderground = (demDF[y][x] - minDEM) * (paraDict['underground_upper']-paraDict['underground_lower']) / (maxDEM-minDEM) + paraDict['underground_lower']
                    # 地下水
                    runoff_groundwater_generate[y][x] =  Q_surf * surfaceToSoil * soilToUnderground
                    # 壤中流
                    runoff_soil_generate[y][x] = Q_surf * surfaceToSoil * (1 - soilToUnderground)
                    # 地表径流
                    # runoff_generate[y][x] = Q_surf - runoff_soil_generate[y][x] - runoff_groundwater_generate[y][x]
                    runoff_generate[y][x] = Q_surf

    pd.DataFrame(runoff_generate).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\runoff_generate.csv')

    # 径流汇流初始化
    runoff_flow = copy.deepcopy(runoff_generate)
    runoff_soil_flow = copy.deepcopy(runoff_soil_generate)
    runoff_groundwater_flow = copy.deepcopy(runoff_groundwater_generate)
    # 水文汇流过程，无拦截损失
    # 地表径流
    def fn(x,y):
        xyCode = fillZero(x,y)
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                runoff_flow[y][x] += fn(preX,preY)
            return runoff_flow[y][x]
        else:
            return runoff_flow[y][x]
    # 壤中流
    def fn2(x,y):
        xyCode = fillZero(x,y)
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                runoff_soil_flow[y][x] += fn2(preX,preY)
            return runoff_soil_flow[y][x]
        else:
            return runoff_soil_flow[y][x]
    # 地下水
    def fn3(x, y):
        xyCode = fillZero(x, y)
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                runoff_groundwater_flow[y][x] += fn3(preX, preY)
            return runoff_groundwater_flow[y][x]
        else:
            return runoff_groundwater_flow[y][x]
    fn(44,209)
    fn2(44,209)
    fn3(44,209)

    pd.DataFrame(runoff_flow).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\runoff_flow.csv')
    print(projectFile+r'\modelResult\month'+str(month)+r'\runoff_flow.csv')
    # 本月的土壤磷循环、施肥措施，生成六个不同的soilP.csv文件
    # 初始化参数
    # 土壤温度
    t_soil = 20
    y_tmp_ly = 0.9 * (t_soil) / (t_soil + math.exp(9.93 - 0.312 * t_soil)) + 0.1  # 3-7
    _trans = paraDict['SOL_BD'] * 10 / 100  # 3-47
    sw_ave = 0.5  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!fake
    FC_ly = 0.4 * paraDict['CLAY'] * paraDict['SOL_BD'] / 100 + paraDict['SOL_AWC']  # 2-103
    if month == 1:
    # 第一个月，初始化P
        minP_act= copy.deepcopy(initDF)
        minP_sta = copy.deepcopy(initDF)
        orgP_hum = copy.deepcopy(initDF)
        orgP_frsh = copy.deepcopy(initDF)
        orgP_act = copy.deepcopy(initDF)
        orgP_sta = copy.deepcopy(initDF)
        P_solution = copy.deepcopy(initDF)
        NO3 = copy.deepcopy(initDF)
        orgN_hum = copy.deepcopy(initDF)
        orgN_act = copy.deepcopy(initDF)
        orgN_sta = copy.deepcopy(initDF)
        orgN_frsh = copy.deepcopy(initDF)
        # 初始化部分库
        for y in range(0,Y):
            for x in range(0,X):
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
            N_input += float(management['fertAmt'])*float(management['fertNtrPer'])
            P_input += float(management['fertAmt'])*float(management['fertPhoPer'])
        NO3_fert_slope = paraDict['FMINN'] * (1 - paraDict['FNH3N']) * N_input
        NH4_fert_slope = paraDict['FMINN'] * (1 - paraDict['FNH3N']) * N_input
        orgN_frsh_slope = 0.5 * paraDict['FORGN'] * N_input
        orgN_act_slope = 0.5 * paraDict['FORGN'] * N_input
        P_solution_slope = paraDict['FMINP'] * P_input
        orgP_frsh_slope = 0.5 * paraDict['FORGP'] * P_input
        orgP_hum_slope =  0.5 * paraDict['FORGP'] *P_input
        # 本月变化
        for y in range(0,Y):
            for x in range(0,X):
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

    # 地表、壤中流、地下水胶体模拟
    colSource_surface = copy.deepcopy(initDF)
    colSource_soil = copy.deepcopy(initDF)
    colSource_underground = copy.deepcopy(initDF)
    slopeColPara = -1 * ((phDict['坡耕地'] - paraDict['para_ph2_col'])*(phDict['坡耕地'] - paraDict['para_ph3_col'])) * paraDict['para_ph4_col']
    paddyColPara = -1 * ((phDict['水田'] - paraDict['para_ph2_col'])*(phDict['水田'] - paraDict['para_ph3_col'])) * paraDict['para_ph4_col']
    forestColPara = -1 * ((phDict['林地'] - paraDict['para_ph2_col'])*(phDict['林地'] - paraDict['para_ph3_col'])) * paraDict['para_ph4_col']
    for y in range(0, Y):
        for x in range(0, X):
            if landuseDF[y][x] == float(forestCode):
                source = forestColPara * rusle[y][x]
                # surfaceToSoil = 1 - math.exp(paraDict['rzlRation'] * (1 - runoff_generate[y][x]))
                surfaceToSoil = (slope[y][x] / 100 + P[y][x]) / 2
                soilToUnderground = (demDF[y][x] - minDEM) * (paraDict['underground_upper'] - paraDict['underground_lower']) / (maxDEM - minDEM) + paraDict['underground_lower']
                surfaceToSoil *= paraDict['rzl_col_ration']
                soilToUnderground *= paraDict['underground_col_ration']
                colSource_soil[y][x] = source * surfaceToSoil * (1 - soilToUnderground)
                colSource_underground[y][x] = colSource_soil[y][x] * soilToUnderground
                colSource_surface[y][x] = source - colSource_soil[y][x] -  colSource_underground[y][x]
            elif landuseDF[y][x] == float(slopelandCode):
                source = slopeColPara * rusle[y][x]
                # surfaceToSoil = 1 - math.exp(paraDict['rzlRation'] * (1 - runoff_generate[y][x]))
                surfaceToSoil = (slope[y][x] / 100 + P[y][x]) / 2
                soilToUnderground = (demDF[y][x] - minDEM) * (
                            paraDict['underground_upper'] - paraDict['underground_lower']) / (maxDEM - minDEM) + \
                                    paraDict['underground_lower']
                surfaceToSoil *= paraDict['rzl_col_ration']
                soilToUnderground *= paraDict['underground_col_ration']
                colSource_soil[y][x] = source * surfaceToSoil * (1 - soilToUnderground)
                colSource_underground[y][x] = colSource_soil[y][x] * soilToUnderground
                colSource_surface[y][x] = source - colSource_soil[y][x] - colSource_underground[y][x]
            elif landuseDF[y][x] == float(paddylandCode):
                source = paddyColPara * rusle[y][x]
                # surfaceToSoil = 1 - math.exp(paraDict['rzlRation'] * (1 - runoff_generate[y][x]))
                surfaceToSoil = (slope[y][x] / 100 + P[y][x]) / 2
                soilToUnderground = (demDF[y][x] - minDEM) * (
                            paraDict['underground_upper'] - paraDict['underground_lower']) / (maxDEM - minDEM) + \
                                    paraDict['underground_lower']
                surfaceToSoil *= paraDict['rzl_col_ration']
                soilToUnderground *= paraDict['underground_col_ration']
                colSource_soil[y][x] = source * surfaceToSoil * (1 - soilToUnderground)
                colSource_underground[y][x] = colSource_soil[y][x] * soilToUnderground
                colSource_surface[y][x] = source - colSource_soil[y][x] - colSource_underground[y][x]
    # 污染源计算，获得solPSource，sedPSource两个DF
    if True:
        solPSource_surface = copy.deepcopy(initDF)
        solPSource_soil = copy.deepcopy(initDF)
        solPSource_underground = copy.deepcopy(initDF)

        sedPSource_surface = copy.deepcopy(initDF)
        sedPSource_soil = copy.deepcopy(initDF)
        sedPSource_underground = copy.deepcopy(initDF)

        colPSource_surface = copy.deepcopy(initDF)
        colPSource_soil = copy.deepcopy(initDF)
        colPSource_underground = copy.deepcopy(initDF)

        for y in range(0, Y):
            for x in range(0, X):
                if initDF[y][x] !=0 or landuseDF[y][x] == waterCode or landuseDF[y][x] == buildingCode or runoff_flow[y][x]==0 or rusle[y][x]==0:
                    continue
                else:
                    conc_sedP = 100 * (minP_act[y][x] + minP_sta[y][x] + orgP_hum[y][x] + orgP_frsh[y][x]) / (
                            paraDict['SOL_BD'] * 10)
                    conc_sedSurf = rusle[y][x] / (10 * 0.09 * runoff_flow[y][x])
                    EPsed = 0.78 * conc_sedSurf ** (-0.2468)
                    solPSource = P_solution[y][x] * runoff_flow[y][x] * 0.09 / (paraDict['SOL_BD'] * 10 * 0.5)
                    sedPSource = 0.0001 * rusle[y][x] * conc_sedP * EPsed
                    colPSource = 0.0001 * (colSource_surface[y][x]+colSource_soil[y][x]+colSource_underground[y][x]) * conc_sedP * EPsed
                    # print(solPSource,sedPSource,colPSource)
                    # surfaceToSoil = 1-math.exp(paraDict['rzlRation']*(1-runoff_generate[y][x]))
                    surfaceToSoil = (slope[y][x] / 100 + P[y][x]) / 2
                    soilToUnderground = (demDF[y][x] - minDEM) * (paraDict['underground_upper']-paraDict['underground_lower']) / (maxDEM-minDEM) + paraDict['underground_lower']

                    solPSource_soil[y][x] = solPSource * surfaceToSoil * (1-soilToUnderground)
                    solPSource_underground[y][x] = solPSource * surfaceToSoil * soilToUnderground
                    solPSource_surface[y][x] = solPSource - solPSource_soil[y][x] - solPSource_underground[y][x]

                    sedPSource_soil[y][x] = sedPSource  * surfaceToSoil * (1-soilToUnderground) * paraDict['rzl_sed_ration']
                    sedPSource_underground[y][x] = sedPSource  * surfaceToSoil * soilToUnderground * paraDict['underground_sed_ration']
                    sedPSource_surface[y][x] = sedPSource - sedPSource_soil[y][x] - sedPSource_underground[y][x]

                    colPSource_soil[y][x] = colPSource  * surfaceToSoil* (1-soilToUnderground) * paraDict['rzl_col_ration']
                    colPSource_underground[y][x] = colPSource  * surfaceToSoil * soilToUnderground * paraDict[
                        'underground_col_ration']
                    colPSource_surface[y][x] = colPSource - colPSource_soil[y][x] - colPSource_underground[y][x]

    # 污染汇
    solPFlow_surface = copy.deepcopy(solPSource_surface)
    colPFlow_surface = copy.deepcopy(colPSource_surface)
    sedPFlow_surface = copy.deepcopy(sedPSource_surface)
    colFlow_surface = copy.deepcopy(colPSource_surface)
    sedFlow = copy.deepcopy(rusle)

    solPFlow_soil = copy.deepcopy(solPSource_soil)
    colPFlow_soil = copy.deepcopy(colPSource_soil)
    sedPFlow_soil = copy.deepcopy(sedPSource_soil)
    colFlow_soil = copy.deepcopy(colPSource_soil)

    solPFlow_underground = copy.deepcopy(solPSource_underground)
    colPFlow_underground = copy.deepcopy(colPSource_underground)
    sedPFlow_underground = copy.deepcopy(sedPSource_underground)
    colFlow_underground = copy.deepcopy(colPSource_underground)

    def flow(x,y):
        xyCode = fillZero(x, y)
        if not slope[y][x] > 0:
            slope[y][x] = 0.01
        if xyCode in transDict:
            fromCode = transDict[xyCode]
            for code in fromCode:
                preX = int(code[1:5])
                preY = int(code[6:])
                preRes = flow(preX,preY)
                solPFlow_surface[y][x] += preRes['solPFlow_surface']
                colPFlow_surface[y][x] += preRes['colPFlow_surface']
                sedPFlow_surface[y][x] += preRes['sedPFlow_surface']
                colFlow_surface[y][x] += preRes['colFlow_surface']
                sedFlow[y][x] += preRes['sedFlow']
                solPFlow_soil[y][x] += preRes['solPFlow_soil']
                colPFlow_soil[y][x] += preRes['colPFlow_soil']
                sedPFlow_soil[y][x] += preRes['sedPFlow_soil']
                colFlow_soil[y][x] += preRes['colFlow_soil']
                solPFlow_underground[y][x] += preRes['solPFlow_underground']
                colPFlow_underground[y][x] += preRes['colPFlow_underground']
                sedPFlow_underground[y][x] += preRes['sedPFlow_underground']
                colFlow_underground[y][x] += preRes['colFlow_underground']

                solPFlow_surface[y][x] *=  0.25 * (1 - paraDict['para_Q1_solP'] ** (-runoff_flow[y][x])
                                                 + paraDict['para_C_solP'] ** (-C[y][x])
                                                 + paraDict['para_S_solP'] ** (-slope[y][x])
                                                 + 1 - paraDict['para_lnconc_solP'] ** (-math.log(solPSource_surface[y][x]) if solPSource_surface[y][x] > 1 else 0))

                colPFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                                        + paraDict['para_C_col'] ** (-C[y][x])
                                        + paraDict['para_S_col'] ** (-slope[y][x])
                                        + 1 - paraDict['para_lnconc_col'] ** (-math.log(colPFlow_surface[y][x]) if colPFlow_surface[y][x] > 1 else 0))

                sedPFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_sedP'] ** (-runoff_flow[y][x])
                                        + paraDict['para_C_sedP'] ** (-C[y][x])
                                        + paraDict['para_S_sedP'] ** (-slope[y][x])
                                        + 1 - paraDict['para_lnconc_sedP'] ** (-math.log(sedPFlow_surface[y][x]) if sedPFlow_surface[y][x] > 1 else 0))

                colFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                                        + paraDict['para_C_col'] ** (-C[y][x])
                                        + paraDict['para_S_col'] ** (-slope[y][x])
                                        + 1 - paraDict['para_lnconc_col'] ** (-math.log(colFlow_surface[y][x]) if colFlow_surface[y][x] > 1 else 0))


                sedFlow[y][x] *= 0.25 * (1 - paraDict['para_Q1_sed'] ** (-runoff_flow[y][x])
                                        + paraDict['para_C_sed'] ** (-C[y][x])
                                        + paraDict['para_S_sed'] ** (-slope[y][x])
                                        + 1 - paraDict['para_lnconc_sed'] ** (-math.log(sedFlow[y][x]) if sedFlow[y][x] > 1 else 0))

                solPFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_solP'] ** (-runoff_flow[y][x])
                                                 + 1 - paraDict['para_lnconc_solP'] ** (-math.log(solPSource_soil[y][x]) if solPSource_soil[y][x] > 1 else 0))


                colPFlow_soil[y][x] *=  0.5 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                                        + 1 - paraDict['para_lnconc_col'] ** (-math.log(colPFlow_soil[y][x]) if colPFlow_soil[y][x] > 1 else 0))

                sedPFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_sedP'] ** (-runoff_flow[y][x])
                                        + 1 - paraDict['para_lnconc_sedP'] ** (-math.log(sedPFlow_soil[y][x]) if sedPFlow_soil[y][x] > 1 else 0))

                colFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                                        + 1 - paraDict['para_lnconc_col'] ** (-math.log(colFlow_soil[y][x]) if colFlow_soil[y][x] > 1 else 0))

            return {
                'solPFlow_surface': solPFlow_surface[y][x],
                'colPFlow_surface': colPFlow_surface[y][x],
                'sedPFlow_surface': sedPFlow_surface[y][x],
                'colFlow_surface': colFlow_surface[y][x],
                'sedFlow': sedFlow[y][x],
                'solPFlow_soil': solPFlow_soil[y][x],
                'colPFlow_soil': colPFlow_soil[y][x],
                'sedPFlow_soil': sedPFlow_soil[y][x],
                'colFlow_soil': colFlow_soil[y][x],
                'solPFlow_underground': solPFlow_underground[y][x],
                'colPFlow_underground': colPFlow_underground[y][x],
                'sedPFlow_underground': sedPFlow_underground[y][x],
                'colFlow_underground': colFlow_underground[y][x],
            }
        else:
            return {
                'solPFlow_surface':solPFlow_surface[y][x],
                'colPFlow_surface':colPFlow_surface[y][x],
                'sedPFlow_surface':sedPFlow_surface[y][x],
                'colFlow_surface':colFlow_surface[y][x],
                'sedFlow':sedFlow[y][x],
                'solPFlow_soil':solPFlow_soil[y][x],
                'colPFlow_soil':colPFlow_soil[y][x],
                'sedPFlow_soil':sedPFlow_soil[y][x],
                'colFlow_soil':colFlow_soil[y][x],
                'solPFlow_underground':solPFlow_underground[y][x],
                'colPFlow_underground':colPFlow_underground[y][x],
                'sedPFlow_underground':sedPFlow_underground[y][x],
                'colFlow_underground':colFlow_underground[y][x],
            }
    flow(44,209)
    # pd.DataFrame(sedPSource_surface).to_csv(r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\sedPSource.csv')
    # pd.DataFrame(sedPFlow_surface).to_csv(r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\sedPFlow.csv')
    # print(colSource_surface[105][50],colFlow_surface[105][50])
    return {
        'minP_act':minP_act,
        'minP_sta':minP_sta,
        'orgP_hum':orgP_hum,
        'orgP_frsh':orgP_frsh,
        'orgP_act':orgP_act,
        'orgP_sta':orgP_sta,
        'P_solution':P_solution,
        'NO3':NO3,
        'orgN_hum':orgN_hum,
        'orgN_act':orgN_act,
        'orgN_sta':orgN_sta,
        'orgN_frsh':orgN_frsh,

        'rusle':rusle,

        'runoff_generate':runoff_generate,
        'runoff_soil_generate':runoff_soil_generate,
        'runoff_groundwater_generate':runoff_groundwater_generate,

        'runoff_flow':runoff_flow,
        'runoff_soil_flow':runoff_soil_flow,
        'runoff_groundwater_flow':runoff_groundwater_flow,

        'colSource_surface':colSource_surface,
        'colSource_soil':colSource_soil,
        'colSource_underground':colSource_underground,

        'solPSource_surface':solPSource_surface,
        'solPSource_soil':solPSource_soil,
        'solPSource_underground':solPSource_underground,
        'sedPSource_surface':sedPSource_surface,
        'sedPSource_soil':sedPSource_soil,
        'sedPSource_underground':sedPSource_underground,
        'colPSource_surface':colPSource_surface,
        'colPSource_soil':colPSource_soil,
        'colPSource_underground':colPSource_underground,

        'solPFlow_surface':solPFlow_surface,
        'colPFlow_surface':colPFlow_surface,
        'sedPFlow_surface':sedPFlow_surface,
        'colFlow_surface':colFlow_surface,
        'sedFlow':sedFlow,
        'solPFlow_soil':solPFlow_soil,
        'colPFlow_soil':colPFlow_soil,
        'sedPFlow_soil':sedPFlow_soil,
        'colFlow_soil':colFlow_soil,
        'solPFlow_underground':solPFlow_underground,
        'colPFlow_underground':colPFlow_underground,
        'sedPFlow_underground':sedPFlow_underground,
        'colFlow_underground':colFlow_underground,


    }

    # 本月的土壤磷、泥沙产生量，生成sedP、solP、sediment csv文件

    # 进行反向递归+拦截模块，生成sedP、solP、sediment的汇流量
# paraList = {
#             'PSP': PSP,  # 0.01-0.7
#             'SOL_SOLP': SOL_SOLP,  # 0-100
#             'SOL_ORGP': SOL_ORGP,  # 0-100
#             'RSDIN': RSDIN,  # 0-10000
#             'SOL_BD': SOL_BD,  # 0.9-2.5
#             'SOL_CBN': SOL_CBN,  # 0.05-10
#             'CMN': CMN,  # 0.001-0.003
#             'CLAY': CLAY,  # 0-100
#             'SOL_AWC': SOL_AWC,  # 0-1
#             'RSDCO': RSDCO,  # 0.02-0.1
#             'RSDCO_PL': RSDCO_PL,  # 0.01-0.099
#             'PPERCO': PPERCO,  # 10-17.5
#             'FMINN': FMINN,  # 0-1
#             'FMINP': FMINP,  # 0-1
#             'FORGN': FORGN,  # 0-1
#             'FORGP': FORGP,  # 0-1
#             'FNH3N': FNH3N,  # 0-1
#             'para_C_sed': para_C_sed,
#             'para_Q1_sed': para_Q1_sed,
#             'para_Q2_sed': para_Q2_sed,
#             'para_lnconc_sed': para_lnconc_sed,
#             'para_S_sed': para_S_sed,
#             'para_C_sedP': para_C_sedP,
#             'para_Q1_sedP': para_Q1_sedP,
#             'para_Q2_sedP': para_Q2_sedP,
#             'para_lnconc_sedP': para_lnconc_sedP,
#             'para_S_sedP': para_S_sedP,
#             'para_C_solP': para_C_solP,
#             'para_Q1_solP': para_Q1_solP,
#             'para_Q2_solP': para_Q2_solP,
#             'para_lnconc_solP': para_lnconc_solP,
#             'para_S_solP': para_S_solP,
# }

def trans(paraDict,x,y):
    resArr = {
        'runoff': {
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        },
        'sedP': {
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
            },
        'solP':{
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        },
        'colP':{
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        },
        'colP_amount':{
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        },
        'TP':{
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        },
        'sed':{
            'surface':[],
            'total':[]
        },
        'col':{
            'surface': [],
            'soil': [],
            'underground': [],
            'total': []
        }
    }
    sedPList = []
    solPList = []
    sedList = []
    colPlist = []
    colList = []
    TPList = []
    for i in range(1,7):
        if i == 1:
            res = oneMonthProcess(paraDict, i,{})
            trans = res['runoff_flow'][184][39] * 1000 * 0.09
            trans2 =  0.09 * 1000000 / res['runoff_flow'][184][39]
            pd.DataFrame(res['runoff_flow']).to_csv(
                r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\runoff.csv')

            resArr['runoff']['surface'].append(float(res['runoff_flow'][x][y]))
            resArr['runoff']['soil'].append(float(res['runoff_soil_flow'][x][y]))
            resArr['runoff']['underground'].append(float(res['runoff_groundwater_flow'][x][y]))
            resArr['runoff']['total'].append(float(res['runoff_flow'][x][y])+float(res['runoff_soil_flow'][x][y])+float(res['runoff_groundwater_flow'][x][y]))

            resArr['solP']['surface'].append(float(res['solPFlow_surface'][x][y]) / trans)
            resArr['solP']['soil'].append(float(res['solPFlow_soil'][x][y]) / trans)
            resArr['solP']['underground'].append(float(res['solPFlow_underground'][x][y]) / trans)
            resArr['solP']['total'].append(float(res['solPFlow_surface'][x][y]+res['solPFlow_soil'][x][y]+res['solPFlow_underground'][x][y]) / trans)
            resArr['sedP']['surface'].append(float(res['sedPFlow_surface'][x][y]) / trans)
            resArr['sedP']['soil'].append(float(res['sedPFlow_soil'][x][y]) / trans)
            resArr['sedP']['underground'].append(float(res['sedPFlow_underground'][x][y]) / trans)
            resArr['sedP']['total'].append(float(res['sedPFlow_surface'][x][y]+res['sedPFlow_soil'][x][y]+res['sedPFlow_underground'][x][y]) / trans)
            resArr['colP']['surface'].append(float(res['colPFlow_surface'][x][y]) / trans)
            resArr['colP']['soil'].append(float(res['colPFlow_soil'][x][y]) / trans)
            resArr['colP']['underground'].append(float(res['colPFlow_underground'][x][y]) / trans)
            resArr['colP']['total'].append(float(res['colPFlow_surface'][x][y]+res['colPFlow_soil'][x][y]+res['colPFlow_underground'][x][y]) / trans)

            resArr['colP_amount']['surface'].append(float(res['colPFlow_surface'][x][y])  * float(res['runoff_flow'][x][y]) / trans)
            resArr['colP_amount']['soil'].append(float(res['colPFlow_soil'][x][y]) * float(res['runoff_soil_flow'][x][y]) / trans)
            resArr['colP_amount']['underground'].append(float(res['colPFlow_underground'][x][y]) * float(res['runoff_groundwater_flow'][x][y]) / trans)
            resArr['colP_amount']['total'].append(
                float(res['colPFlow_surface'][x][y] * res['runoff_flow'][x][y] + res['colPFlow_soil'][x][y] *res['runoff_soil_flow'][x][y]
                      + res['colPFlow_underground'][x][y] * res['runoff_groundwater_flow'][x][y]) / trans)

            resArr['TP']['surface'].append(float(res['solPFlow_surface'][x][y]+res['sedPFlow_surface'][x][y]+res['colPFlow_surface'][x][y]) / trans)
            resArr['TP']['soil'].append(float(res['solPFlow_soil'][x][y]+res['sedPFlow_soil'][x][y]+res['colPFlow_soil'][x][y]) / trans)
            resArr['TP']['underground'].append(float(res['solPFlow_underground'][x][y]+res['sedPFlow_underground'][x][y]+res['colPFlow_underground'][x][y]) / trans)
            resArr['TP']['total'].append(float(res['colPFlow_surface'][x][y]+res['colPFlow_soil'][x][y]+res['colPFlow_underground'][x][y]+
                                         res['solPFlow_soil'][x][y] + res['sedPFlow_soil'][x][y] + res['colPFlow_soil'][x][y]+
                                         res['solPFlow_underground'][x][y] + res['sedPFlow_underground'][x][y] +res['colPFlow_underground'][x][y]) / trans
                                         )
            resArr['sed']['surface'].append(float(res['sedFlow'][x][y]) * trans2)
            resArr['sed']['total'].append(float(res['sedFlow'][x][y]) * trans2)
            resArr['col']['surface'].append(float(res['colFlow_surface'][x][y]) * trans2)
            resArr['col']['soil'].append(float(res['colFlow_soil'][x][y]) * trans2)
            resArr['col']['underground'].append(float(res['colFlow_underground'][x][y]) * trans2)
            resArr['col']['total'].append(float(res['colFlow_surface'][x][y]+res['colFlow_soil'][x][y]+res['colFlow_underground'][x][y]) * trans2)
        else:
            res = oneMonthProcess(paraDict,i,res)
            trans = res['runoff_flow'][184][39] * 1000 * 0.09
            trans2 =  0.09 * 1000000 / res['runoff_flow'][184][39]
            resArr['runoff']['surface'].append(float(res['runoff_flow'][x][y]))
            resArr['runoff']['soil'].append(float(res['runoff_soil_flow'][x][y]))
            resArr['runoff']['underground'].append(float(res['runoff_groundwater_flow'][x][y]))
            resArr['runoff']['total'].append(float(res['runoff_flow'][x][y])+float(res['runoff_soil_flow'][x][y])+float(res['runoff_groundwater_flow'][x][y]))
            resArr['solP']['surface'].append(float(res['solPFlow_surface'][x][y]) / trans)
            resArr['solP']['soil'].append(float(res['solPFlow_soil'][x][y]) / trans)
            resArr['solP']['underground'].append(float(res['solPFlow_underground'][x][y]) / trans)
            resArr['solP']['total'].append(
                float(res['solPFlow_surface'][x][y] + res['solPFlow_soil'][x][y] + res['solPFlow_underground'][x][y]) / trans)
            resArr['sedP']['surface'].append(float(res['sedPFlow_surface'][x][y]) / trans)
            resArr['sedP']['soil'].append(float(res['sedPFlow_soil'][x][y]) / trans)
            resArr['sedP']['underground'].append(float(res['sedPFlow_underground'][x][y]) / trans)
            resArr['sedP']['total'].append(
                float(res['sedPFlow_surface'][x][y] + res['sedPFlow_soil'][x][y] + res['sedPFlow_underground'][x][y]) / trans)
            resArr['colP']['surface'].append(float(res['colPFlow_surface'][x][y]) / trans)
            resArr['colP']['soil'].append(float(res['colPFlow_soil'][x][y]) / trans)
            resArr['colP']['underground'].append(float(res['colPFlow_underground'][x][y]) / trans)

            resArr['colP_amount']['surface'].append(
                float(res['colPFlow_surface'][x][y]) * float(res['runoff_flow'][x][y]) / trans)
            resArr['colP_amount']['soil'].append(
                float(res['colPFlow_soil'][x][y]) * float(res['runoff_soil_flow'][x][y]) / trans)
            resArr['colP_amount']['underground'].append(
                float(res['colPFlow_underground'][x][y]) * float(res['runoff_groundwater_flow'][x][y]) / trans)
            resArr['colP_amount']['total'].append(
                float(res['colPFlow_surface'][x][y] * res['runoff_flow'][x][y] + res['colPFlow_soil'][x][y] *
                      res['runoff_soil_flow'][x][y]
                      + res['colPFlow_underground'][x][y] * res['runoff_groundwater_flow'][x][y]) / trans)

            resArr['TP']['surface'].append(
                float(res['solPFlow_surface'][x][y] + res['sedPFlow_surface'][x][y] + res['colPFlow_surface'][x][y]) / trans)
            resArr['TP']['soil'].append(
                float(res['solPFlow_soil'][x][y] + res['sedPFlow_soil'][x][y] + res['colPFlow_soil'][x][y]) / trans)
            resArr['TP']['underground'].append(float(
                res['solPFlow_underground'][x][y] + res['sedPFlow_underground'][x][y] + res['colPFlow_underground'][x][
                    y]) / trans)
            resArr['TP']['total'].append(
                float(res['colPFlow_surface'][x][y] + res['colPFlow_soil'][x][y] + res['colPFlow_underground'][x][y] +
                      res['solPFlow_soil'][x][y] + res['sedPFlow_soil'][x][y] + res['colPFlow_soil'][x][y] +
                      res['solPFlow_underground'][x][y] + res['sedPFlow_underground'][x][y] +
                      res['colPFlow_underground'][x][y]) / trans
                )
            resArr['sed']['surface'].append(float(res['sedFlow'][x][y]) * trans2)
            resArr['sed']['total'].append(float(res['sedFlow'][x][y]) * trans2)
            resArr['col']['surface'].append(float(res['colFlow_surface'][x][y]) * trans2)
            resArr['col']['soil'].append(float(res['colFlow_soil'][x][y]) * trans2)
            resArr['col']['underground'].append(float(res['colFlow_underground'][x][y]) * trans2)
            resArr['col']['total'].append(
                float(res['colFlow_surface'][x][y] + res['colFlow_soil'][x][y] + res['colFlow_underground'][x][y]) * trans2)


    return resArr

# 定义几个率定变量
objective_r2_TP = []
objective_nse_TP = []
objective_r2_sedP = []
objective_nse_sedP = []
objective_r2_solP = []
objective_nse_solP = []
objective_r2_sed = []
objective_nse_sed = []
objective_r2_colP = []
objective_nse_colP = []
objective_r2_col = []
objective_nse_col = []

SimulateSed = []
SimulateSedP = []
SimulateSolP = []
SimulateColP = []
SimulateCol = []
SimulateTP = []



def r2(obs, pre,key):
    fenMu1 = 0
    fenMu2 = 0
    fenZi = 0
    obsMean = np.mean(obs)
    preMean = np.mean(pre)
    for i in range(0, len(obs)):
        fenZi += (obs[i] - obsMean) * (pre[i] - preMean)
        fenMu1 += abs(obs[i] - obsMean) ** 2
        fenMu2 +=  abs(pre[i] - preMean) ** 2
    fenMu = (fenMu1**0.5)*(fenMu2**0.5)
    print(key,'r2', (fenZi / fenMu) ** 2,obs,pre)
    return -(fenZi / fenMu) ** 2

def NSE(obs, pre,key):
    fenMu = 0
    fenZi = 0
    obsMean = np.mean(obs)
    for i in range(0, len(obs)):
        fenZi += (pre[i] - obs[i]) ** 2
        fenMu += (obs[i] - obsMean) ** 2
    print(key,'nse', (1 - fenZi / fenMu),obs,pre)
    return -(1 - fenZi / fenMu)

def RE(obs, pre,key):
    re = 0
    for i in range(0, len(obs)):
        re += abs((pre[i]-obs[i]) / obs[i])
    print(key,'RE',re / len(obs),obs,pre )
    return -re / len(obs)

def process(PSP, SOL_SOLP, SOL_ORGP, RSDIN, SOL_BD, SOL_CBN, CMN, CLAY, SOL_AWC, RSDCO, RSDCO_PL, PPERCO, # 0 - 12
            FMINN, FMINP, FORGN, FORGP, FNH3N, # 13 - 17
            para_C_sed, para_Q1_sed, para_Q2_sed, para_lnconc_sed, para_S_sed, # 18 - 22
            para_C_sedP,para_Q1_sedP, para_Q2_sedP, para_lnconc_sedP, para_S_sedP, # 23 - 27
            para_C_solP, para_Q1_solP, para_Q2_solP,para_lnconc_solP, para_S_solP, # 28 - 32
            rationSed,rationSedP,rationSolP, # 33 - 35
            rationSurfaceToSoil,rationSoilToUndergroud,  # 36 - 37
            CN1,CN2,CN3,  # 38 - 40
            para_ph1_col,para_ph2_col,para_ph3_col,para_ph4_col,   # 41 - 44
            para_C_col, para_Q1_col, para_Q2_col, para_lnconc_col, para_S_col, # 45 - 49
            para_C_colP,para_Q1_colP, para_Q2_colP, para_lnconc_colP, para_S_colP, # 50 - 54
            rzlRation,rzl_col_ration,rzl_sed_ration,rzl_threshold, # 55 - 58
            underground_lower,underground_upper,underground_sed_ration,underground_col_ration, # 59-62
            final_ration1,final_ration2
            ):
    global objective_r2_sedP,objective_nse_sedP,\
    objective_r2_solP,objective_nse_solP,objective_r2_sed,\
    objective_nse_sed,objective_r2_colP,objective_nse_colP,\
    objective_r2_col,objective_nse_col
    time = 0
    objective = {}
    for key in celibratedTarget:
        objective[key] = {
            'r2':[],
            'nse':[],
            're':[]
        }
    allRes = []
    paraRes = []
    for PSP, SOL_SOLP, SOL_ORGP, RSDIN, SOL_BD, SOL_CBN, CMN, CLAY, SOL_AWC, RSDCO, RSDCO_PL, PPERCO, \
        FMINN, FMINP, FORGN, FORGP, FNH3N, \
        para_C_sed, para_Q1_sed, para_Q2_sed, para_lnconc_sed, para_S_sed, \
        para_C_sedP, para_Q1_sedP, para_Q2_sedP, para_lnconc_sedP, para_S_sedP, \
        para_C_solP, para_Q1_solP, para_Q2_solP, para_lnconc_solP, para_S_solP, \
        rationSed, rationSedP, rationSolP, rationSurfaceToSoil, rationSoilToUndergroud, CN1, CN2, CN3, \
        para_ph1_col, para_ph2_col, para_ph3_col, para_ph4_col, \
        para_C_col, para_Q1_col, para_Q2_col, para_lnconc_col, para_S_col, \
        para_C_colP, para_Q1_colP, para_Q2_colP, para_lnconc_colP, para_S_colP, \
        rzlRation, rzl_col_ration, rzl_sed_ration, rzl_threshold, \
        underground_lower, underground_upper, underground_sed_ration, underground_col_ration,final_ration1,final_ration2 in zip(
        PSP, SOL_SOLP, SOL_ORGP, RSDIN, SOL_BD, SOL_CBN, CMN, CLAY, SOL_AWC, RSDCO, RSDCO_PL, PPERCO,
        FMINN, FMINP, FORGN, FORGP, FNH3N,
        para_C_sed, para_Q1_sed, para_Q2_sed, para_lnconc_sed, para_S_sed,
        para_C_sedP, para_Q1_sedP, para_Q2_sedP, para_lnconc_sedP, para_S_sedP,
        para_C_solP, para_Q1_solP, para_Q2_solP, para_lnconc_solP, para_S_solP,
        rationSed, rationSedP, rationSolP, rationSurfaceToSoil, rationSoilToUndergroud, CN1, CN2, CN3,
        para_ph1_col, para_ph2_col, para_ph3_col, para_ph4_col,
        para_C_col, para_Q1_col, para_Q2_col, para_lnconc_col, para_S_col,  # 45 - 49
        para_C_colP, para_Q1_colP, para_Q2_colP, para_lnconc_colP, para_S_colP,  # 50 - 54
        rzlRation, rzl_col_ration, rzl_sed_ration, rzl_threshold,
        underground_lower, underground_upper, underground_sed_ration, underground_col_ration,
        final_ration1, final_ration2
    ):
        time += 1
        # 一组参数
        paraDict = {
            'PSP': PSP,  # 0.01-0.7
            'SOL_SOLP': SOL_SOLP,  # 0-100
            'SOL_ORGP': SOL_ORGP,  # 0-100
            'RSDIN': RSDIN,  # 0-10000
            'SOL_BD': SOL_BD,  # 0.9-2.5
            'SOL_CBN': SOL_CBN,  # 0.05-10
            'CMN': CMN,  # 0.001-0.003
            'CLAY': CLAY,  # 0-100
            'SOL_AWC': SOL_AWC,  # 0-1
            'RSDCO': RSDCO,  # 0.02-0.1
            'RSDCO_PL': RSDCO_PL,  # 0.01-0.099
            'PPERCO': PPERCO,  # 10-17.5
            'FMINN': FMINN,  # 0-1
            'FMINP': FMINP,  # 0-1
            'FORGN': FORGN,  # 0-1
            'FORGP': FORGP,  # 0-1
            'FNH3N': FNH3N,  # 0-1
            'para_C_sed': para_C_sed,
            'para_Q1_sed': para_Q1_sed,
            'para_Q2_sed': para_Q2_sed,
            'para_lnconc_sed': para_lnconc_sed,
            'para_S_sed': para_S_sed,
            'para_C_sedP': para_C_sedP,
            'para_Q1_sedP': para_Q1_sedP,
            'para_Q2_sedP': para_Q2_sedP,
            'para_lnconc_sedP': para_lnconc_sedP,
            'para_S_sedP': para_S_sedP,
            'para_C_solP': para_C_solP,
            'para_Q1_solP': para_Q1_solP,
            'para_Q2_solP': para_Q2_solP,
            'para_lnconc_solP': para_lnconc_solP,
            'para_S_solP': para_S_solP,
            'rationSed': rationSed,
            'rationSedP': rationSedP,
            'rationSolP': rationSolP,
            'rationSurfaceToSoil': rationSurfaceToSoil,
            'rationSoilToUndergroud': rationSoilToUndergroud,
            'CN1': CN1,
            'CN2': CN2,
            'CN3': CN3,
            'para_ph1_col': para_ph1_col,
            'para_ph2_col': para_ph2_col,
            'para_ph3_col': para_ph3_col,
            'para_ph4_col': para_ph4_col,
            'para_C_col': para_C_col,
            'para_Q1_col': para_Q1_col,
            'para_Q2_col': para_Q2_col,
            'para_lnconc_col': para_lnconc_col,
            'para_S_col': para_S_col,
            'para_C_colP': para_C_colP,
            'para_Q1_colP': para_Q1_colP,
            'para_Q2_colP': para_Q2_colP,
            'para_lnconc_colP': para_lnconc_colP,
            'para_S_colP': para_S_colP,
            'rzlRation':rzlRation,
            'rzl_col_ration':rzl_col_ration,
            'rzl_sed_ration':rzl_sed_ration,
            'rzl_threshold':rzl_threshold,
            'underground_lower':underground_lower,
            'underground_upper':underground_upper,
            'underground_sed_ration':underground_sed_ration,
            'underground_col_ration':underground_col_ration,
            'final_ration1':final_ration1,
            'final_ration2':final_ration2
        }
        paraRes.append(paraDict)
        # 关键传输函数，返回一整次模拟的所有结果
        res = trans(paraDict, 209, 44)
        print('径流',res['runoff']['total'])
        allRes.append(res)
        # global SimulateSed,SimulateSedP,SimulateSolP,SimulateColP,SimulateCol
        newColPArr = [0,0,0,0,0,0]
        # for i in range(0, len(celibratedValue['colP'])):
        #     res['colP_amount']['total'][i] *= paraDict['final_ration1']
        #     res['colP_amount']['surface'][i] *= paraDict['final_ration1']
        #     res['colP_amount']['underground'][i] *= paraDict['final_ration1']
        #     res['colP_amount']['soil'][i] *= paraDict['final_ration1']
        #     newColPArr[i] = celibratedValue['colP'][i] * res['runoff']['total'][i]


        # objective[key]['r2'].append(r2(newColPArr, res['colP_amount']['total']))
        # objective[key]['nse'].append(NSE(newColPArr, res['colP_amount']['total']))
        # objective[key]['re'].append(RE(newColPArr, res['colP_amount']['total']))

        for key in celibratedTarget:
            objective[key]['r2'].append(r2(celibratedValue[key], res[key]['total'],key))
            objective[key]['nse'].append(NSE(celibratedValue[key], res[key]['total'],key))
            objective[key]['re'].append(RE(celibratedValue[key], res[key]['total'],key))
        print(res)
        # print('率定结果colP', res['colP'])
        # print('率定结果colP_amount1', res['colP_amount'])
        # print('率定结果colP_amount2', res['colP_amount']['total'])
        # print('率定结果runoff', res['runoff'])
        # print('率定结果所有结果', res)
        # print('观测结果', newColPArr)
        # print('率定参数', paraDict)
        # print('-----------------------------------')

    return [objective,allRes,paraRes]


        #
        # start = datetime.datetime.now()
        # res = trans(paraDict, 209, 44)
        #
        # # res = [[1],[1],[1]]
        # end = datetime.datetime.now()
        # sedP = [i * paraDict['rationSedP'] for i in res[0]]
        # solP = [i * paraDict['rationSedP'] for i in res[1]]
        # sed = [i * paraDict['rationSedP'] for i in res[2]]
        #
        # global calibratesTimes
        # calibratesTimes = 1 + calibratesTimes
        # jsonData = {
        #     'paraDict': paraDict,
        #     'sedP_r2': r2(sedP, sedP_obs),
        #     'solP_r2': r2(solP, solP_obs),
        #     'sedP_NSE': NSE(sedP, sedP_obs),
        #     'solP_NSE': NSE(solP, solP_obs),
        # }
        # if not os.path.exists(projectFile + r'/calibrateJson'):
        #     os.mkdir(projectFile + r'/calibrateJson')
        # with open(projectFile + r'/calibrateJson/calibrate_result' + str(calibratesTimes) + '.json', "w") as f:
        #     json.dump(jsonData, f)



# 率定模块
import autograd.numpy as anp
from pymoo.core.problem import Problem
celibratedTimes = 0
class MyProblem(Problem):
    def __init__(self):
        super().__init__(
            n_var=64,
            n_obj=len(celibratedTarget)*3,
            xl=anp.array(
                [0.01, # PSP 1
                 70, # SOL_SOLP 2
                 0, #SOL_ORGP 3
                 0, # RSDIN 4
                 1.2, # SOL_BD 5
                 3, # SOL_CBN 6
                 0.001, # CMN 7
                 90, # CLAY 8
                 0, # SOL_AWC 9
                 0.02, # RSDCO 10
                 0.01, # RSDCO_PL 11
                 10, # PPERCO 12
                 0, # FMINN 13
                 0, # FMINP 14
                 0, # FORGN 15
                 0, # FORGP 16
                 0, # FNH3N 17
                 1, 1, 1, 1, 1, # 五个sed_para 18-22
                 1, 1, 1, 1, 1, # 五个sedP_para 23-27
                 1, 1, 1, 1, 1, # 五个solP_para 28-32
                 0, 0, 0, #最终结果比例 33-35
                 0, #表层->包气带的下渗比例 36
                 0,  #包气带->浅层地下水的比例 37
                 30, #CN1 38
                 30, #CN2 39
                 30,  #CN3 40
                 -1,2,9,0, # -a(x-b)(x-c) * (0~1) ph范围与胶体 41-44
                 1, 1, 1, 1, 1,  # 五个colP_para 45-49
                 1, 1, 1, 1, 1,  # 五个col_para 50-54
                 0,0,0,0, # 1 - e^(a-a*x) 壤中流的比例随着降雨量增加而增加，后两个参数为胶体、大颗粒进入壤中流 和 径流/溶解态进入壤中流的比例，最后一个参数是产生壤中流的下限
                 0,0.51,0,0, # 壤中流进入地下水的下界/上界，胶体、大颗粒的比例
                 0.0000001,0.0000001 #FINAL_RATION
                 ]),  # 变量下界
            xu=anp.array(
                [0.5, # PSP
                 90,  # SOL_SOLP
                 100, #SOL_ORGP
                 10000, # RSDIN
                 1.9, # SOL_BD
                 4, # SOL_CBN
                 0.003,  # CMN
                 100,  # CLAY
                 1, # SOL_AWC
                 0.1,  # RSDCO
                 0.099,  # RSDCO_PL
                 12,  # PPERCO
                 1, # FMINN
                 1, # FMINP
                 1, # FORGN
                 1, # FORGP
                 1,# FNH3N
                 2, 2, 2, 2, 2,
                 2, 2, 2, 2, 2,
                 2, 2, 2, 2, 2,
                 1, 1, 1,
                 1,
                 1,
                 90,
                 90,
                 90,
                 -1,4,11,0.08,
                 2, 2, 2, 2, 2,
                 2, 2, 2, 2, 2,
                 0.1,3,3,30,
                 0.49,0.99,3,3,
                 10000,10000
                 ]),  # 变量上界
        )

    def _evaluate(self, x, out, *args, **kwargs):
        [objective,allRes,paraRes] = process(x[:, 0], x[:, 1], x[:, 2], x[:, 3], x[:, 4], x[:, 5], x[:, 6], x[:, 7], x[:, 8], x[:, 9], x[:, 10],
                     x[:, 11],x[:, 12], x[:, 13],x[:, 14],x[:, 15], x[:, 16],
                     x[:, 17], x[:, 18],x[:, 19],x[:, 20],x[:, 21],
                     x[:, 22], x[:, 23], x[:, 24],x[:, 25], x[:, 26],
                     x[:, 27], x[:, 28],x[:, 29],x[:, 30], x[:, 31],
                     x[:,32],x[:, 33],x[:,34],x[:, 35],x[:,36],x[:,37],x[:, 38],x[:,39],
                     x[:,40],x[:,41],x[:, 42],x[:,43],
                     x[:, 44], x[:, 45], x[:, 46], x[:, 47], x[:, 48],
                     x[:, 49], x[:, 50], x[:, 51], x[:, 52], x[:, 53],
                     x[:, 54], x[:, 55], x[:, 56], x[:, 57],
                     x[:, 58], x[:, 59], x[:, 60], x[:, 61],
                     x[:, 62], x[:, 63]
                   )
        path = projectFile + r'\modelResult\celibrateJson.json'
        path2 = projectFile + r'\modelResult\r2_nse.json'
        path3 = projectFile + r'\modelResult\parameters.json'

        if os.path.exists(path):
            with open(path, 'r') as load_f:
                load_dict = json.load(load_f)
                load_dict.extend(allRes)
                f = open(path, 'w')
                f.write(json.dumps(load_dict))
                f.close()
        else:
            f = open(path, 'w')
            f.write(json.dumps(allRes))
            f.close()

        # if os.path.exists(path3):
        #     with open(path3, 'r') as load_f:
        #         load_dict = json.load(load_f)
        #         load_dict.extend(paraRes)
        #         f = open(path3, 'w')
        #         f.write(json.dumps(load_dict))
        #         f.close()
        # else:
        #     f = open(path3, 'w')
        #     f.write(json.dumps(paraRes))
        #     f.close()
        #
        # if os.path.exists(path2):
        #     with open(path2, 'r') as load_f:
        #         load_dict = json.load(load_f)
        #         for key in load_dict:
        #             load_dict[key]['r2'].extend(objective[key]['r2'])
        #             load_dict[key]['nse'].extend(objective[key]['nse'])
        #         f = open(path2, 'w')
        #         f.write(json.dumps(load_dict))
        #         f.close()
        # else:
        #     f = open(path2, 'w')
        #     f.write(json.dumps(objective))
        #     f.close()

        r2_nse_arr = []
        for key in celibratedTarget:
            r2_nse_arr.append(objective[key]['r2'])
            r2_nse_arr.append(objective[key]['nse'])
            r2_nse_arr.append(-objective[key]['re'])

        out["F"] = anp.column_stack(r2_nse_arr)
        global celibratedTimes
        celibratedTimes+=1
        time.sleep(1)
        print('signal',celibratedTimes,r2_nse_arr,'start',flush=True)


from pymoo.algorithms.moo.nsga2 import NSGA2  # 最新版已经发生改变
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.optimize import minimize

# 定义遗传算法
algorithm = NSGA2(
    pop_size=300,
    n_offsprings=10,
    sampling=get_sampling("real_random"),
    crossover=get_crossover("real_sbx", prob=0.9, eta=15),
    mutation=get_mutation("real_pm", eta=20),
    eliminate_duplicates=True
)


# 求解方程
res = minimize(MyProblem(),
               algorithm,
               ('n_gen', 500),
               seed=1,
               return_least_infeasible=True,  # 在固定的迭代次数没有完成之前，算出最小值
               verbose=True
               )
# 取消警告
from pymoo.config import Config
Config.show_compile_hint = False
# print(res)
print('res.X', res.X)
print('res.F', res.F)  # 显示结果
