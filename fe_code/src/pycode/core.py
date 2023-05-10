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
projectName = projectFile.split('\\')[-1]
fileList = os.listdir(projectFile+r'\observeData')
# 施肥措施数据
allProjectInfo = []
with open(r'E:\webplatform\fe_code\projectInfo.json','r',encoding='utf-8') as fp:
    allProjectInfo = json.load(fp)
curProjectInfo = list(filter(lambda info: info["projectName"] == projectName,allProjectInfo))[0]

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
C_factorDF = pd.read_csv(projectFile + r'\database\C_factor_10000times.csv',index_col=0).values
K_factorDF = pd.read_csv(projectFile + r'\database\K_factor_10000times.csv',index_col=0).values
L_factorDF = pd.read_csv(projectFile + r'\database\L_factor_10000times.csv',index_col=0).values
S_factorDF = pd.read_csv(projectFile + r'\database\S_factor_10000times.csv',index_col=0).values
P_factorDF = pd.read_csv(projectFile + r'\database\P_factor_10000times.csv',index_col=0).values

demDF = pd.read_csv(projectFile+r'\database\DEM.csv',index_col=0).values
slopeDF = pd.read_csv(projectFile+r'\database\slope.csv',index_col=0).values

[X,Y,initDF] = utils.checkAreaMatch(
    [landuseDF,d8DF,C_factorDF,K_factorDF,L_factorDF,S_factorDF,demDF,slopeDF],
    ["土地利用类型","D8","C因子","K因子","L因子","S因子","DEM","坡度"],
)
# 获取时间跨度
dateRange = []
with open(projectFile+r'\database\R_factor.txt', "r", encoding="utf-8") as f:
    dateRange = json.load(f)
phDict = {
    '坡耕地':5.75,
    '林地':6.46,
    '水田':5.57
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

# 获得土地利用类型 code - landuse 对应字典
landuseDict = utils.getLanduseCode(curProjectInfo)
landuseDictDemo = {'1': 'forest',
 '2': 'sloping',
 '3': 'water',
 '4': 'paddy',
 '5': 'construct'}
for item in landuseDict.items():
    if item[1]=='forest':
        forestCode = item[0]
    elif item[1]=='sloping':
        slopelandCode = item[0]
    elif item[1]=='paddy':
        paddylandCode = item[0]
    elif item[1] == 'water':
        waterCode = item[0]
    elif item[1] == 'construct':
        buildingCode = item[0]
# 施肥措施数据
managementDict = utils.getManagementInfo(curProjectInfo)

# eg.
# mgt = {
#     'name': '1',
#     'amount': '300',
#     'applyMonth': 6,
#     'N_ration': '0.4',
#     'P_ration': '0.6',
# }
# 日期数据
[startDateTime,endDateTime] = utils.getDataRange(curProjectInfo)
monthRainfall = utils.getMonthlyRainfall(projectFile,curProjectInfo)
# 创建空文件夹
utils.createResultFile(projectFile,len(monthRainfall))
# 开始汇流计算
def oneMonthProcess(paraDict,month,preMonthResult):
    # 读取rusle数据
    rusle = pd.read_csv(projectFile+r'\rusle\rusle'+str(month)+'.csv',index_col=0).values
    # 基于D8计算每个月的降雨产流，生成runoff.csv文件
    # 地表径流、壤中流产流
    runoff_generate = copy.deepcopy(initDF)
    runoff_soil_generate = copy.deepcopy(initDF)
    rainfall = monthRainfall[month - 1]['rainfall']

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
    pd.DataFrame(runoff_generate).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\地表径流_产生量.csv')
    pd.DataFrame(runoff_soil_generate).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\壤中流_产生量.csv')
    # 地表径流、壤中流汇流
    runoff_flow = copy.deepcopy(runoff_generate)
    runoff_soil_flow = copy.deepcopy(runoff_soil_generate)
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
    pd.DataFrame(runoff_flow).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\地表径流_汇流量.csv')
    pd.DataFrame(runoff_soil_flow).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\壤中流_汇流量.csv')

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

    # 地表、壤中流、地下水胶体模拟
    colSource_surface = copy.deepcopy(initDF)
    colSource_soil = copy.deepcopy(initDF)

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
    # 污染源计算，获得solPSource，sedPSource两个DF
    if True:
        solPSource_surface = copy.deepcopy(initDF)
        solPSource_soil = copy.deepcopy(initDF)

        sedPSource_surface = copy.deepcopy(initDF)
        sedPSource_soil = copy.deepcopy(initDF)

        colPSource_surface = copy.deepcopy(initDF)
        colPSource_soil = copy.deepcopy(initDF)

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
                if initDF[y][x] !=0 or landuseDF[y][x] == waterCode or landuseDF[y][x] == buildingCode or runoff_flow[y][x]==0 or rusle[y][x]==0:
                    continue
                else:
                    conc_sedP = 100 * (minP_act[y][x] + minP_sta[y][x] + orgP_hum[y][x] + orgP_frsh[y][x]) / (
                            paraDict['SOL_BD'] * 10)
                    conc_sedSurf = rusle[y][x] / (10 * 0.09 * runoff_flow[y][x])
                    EPsed = 0.78 * conc_sedSurf ** (-0.2468)
                    solPSource = P_solution[y][x] * runoff_flow[y][x] * 0.09 / (paraDict['SOL_BD'] * 10 * 0.5)
                    sedPSource = 0.0001 * rusle[y][x] * conc_sedP * EPsed
                    colPSource = 0.0001 * (colSource_surface[y][x]+colSource_soil[y][x]) * conc_sedP * EPsed


                    solPSource_soil[y][x] = solPSource * soil_ratio
                    solPSource_surface[y][x] = solPSource * runoff_ratio

                    sedPSource_soil[y][x] = sedPSource * soil_ratio
                    sedPSource_surface[y][x] = sedPSource * runoff_ratio

                    colPSource_soil[y][x] = colPSource * soil_ratio
                    colPSource_surface[y][x] = colPSource * runoff_ratio
    # 污染汇
    solPFlow_surface = copy.deepcopy(solPSource_surface)
    colPFlow_surface = copy.deepcopy(colPSource_surface)
    sedPFlow_surface = copy.deepcopy(sedPSource_surface)
    # colFlow_surface = copy.deepcopy(colPSource_surface)
    # sedFlow = copy.deepcopy(rusle)
    solPFlow_soil = copy.deepcopy(solPSource_soil)
    colPFlow_soil = copy.deepcopy(colPSource_soil)
    sedPFlow_soil = copy.deepcopy(sedPSource_soil)
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

                solPFlow_surface[y][x] = solP_loss * runoff_ratio
                colPFlow_surface[y][x] = colP_loss * runoff_ratio
                sedPFlow_surface[y][x] = sedP_loss * runoff_ratio
                solPFlow_soil[y][x] = solP_loss * soil_ratio
                colPFlow_soil[y][x] = colP_loss * soil_ratio
                sedPFlow_soil[y][x] = sedP_loss * soil_ratio

                #
                #
                # solPFlow_surface[y][x] *=  0.25 * (1 - paraDict['para_Q1_solP'] ** (-runoff_flow[y][x])
                #                                  + paraDict['para_C_solP'] ** (-C_factorDF[y][x] / 10000)
                #                                  + paraDict['para_S_solP'] ** (-slopeDF[y][x])
                #                                  + 1 - paraDict['para_lnconc_solP'] ** (-math.log(solPSource_surface[y][x]) if solPSource_surface[y][x] > 1 else 0))
                # colPFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                #                         + paraDict['para_C_col'] ** (-C_factorDF[y][x])
                #                         + paraDict['para_S_col'] ** (-slopeDF[y][x])
                #                         + 1 - paraDict['para_lnconc_col'] ** (-math.log(colPFlow_surface[y][x]) if colPFlow_surface[y][x] > 1 else 0))
                #
                # sedPFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_sedP'] ** (-runoff_flow[y][x])
                #                         + paraDict['para_C_sedP'] ** (-C_factorDF[y][x])
                #                         + paraDict['para_S_sedP'] ** (-slopeDF[y][x])
                #                         + 1 - paraDict['para_lnconc_sedP'] ** (-math.log(sedPFlow_surface[y][x]) if sedPFlow_surface[y][x] > 1 else 0))
                #
                # colFlow_surface[y][x] *= 0.25 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                #                         + paraDict['para_C_col'] ** (-C_factorDF[y][x])
                #                         + paraDict['para_S_col'] ** (-slopeDF[y][x])
                #                         + 1 - paraDict['para_lnconc_col'] ** (-math.log(colFlow_surface[y][x]) if colFlow_surface[y][x] > 1 else 0))
                #
                #
                # sedFlow[y][x] *= 0.25 * (1 - paraDict['para_Q1_sed'] ** (-runoff_flow[y][x])
                #                         + paraDict['para_C_sed'] ** (-C_factorDF[y][x])
                #                         + paraDict['para_S_sed'] ** (-slopeDF[y][x])
                #                         + 1 - paraDict['para_lnconc_sed'] ** (-math.log(sedFlow[y][x]) if sedFlow[y][x] > 1 else 0))
                #
                # solPFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_solP'] ** (-runoff_flow[y][x])
                #                                  + 1 - paraDict['para_lnconc_solP'] ** (-math.log(solPSource_soil[y][x]) if solPSource_soil[y][x] > 1 else 0))
                #
                #
                # colPFlow_soil[y][x] *=  0.5 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                #                         + 1 - paraDict['para_lnconc_col'] ** (-math.log(colPFlow_soil[y][x]) if colPFlow_soil[y][x] > 1 else 0))
                #
                # sedPFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_sedP'] ** (-runoff_flow[y][x])
                #                         + 1 - paraDict['para_lnconc_sedP'] ** (-math.log(sedPFlow_soil[y][x]) if sedPFlow_soil[y][x] > 1 else 0))
                #
                # colFlow_soil[y][x] *= 0.5 * (1 - paraDict['para_Q1_col'] ** (-runoff_flow[y][x])
                #                         + 1 - paraDict['para_lnconc_col'] ** (-math.log(colFlow_soil[y][x]) if colFlow_soil[y][x] > 1 else 0))

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
    # pd.DataFrame(sedPSource_surface).to_csv(r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\sedPSource.csv')
    # pd.DataFrame(sedPFlow_surface).to_csv(r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\sedPFlow.csv')
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

        'runoff_flow':runoff_flow,
        'runoff_soil_flow':runoff_soil_flow,

        'colSource_surface':colSource_surface,
        'colSource_soil':colSource_soil,

        'solPSource_surface':solPSource_surface,
        'solPSource_soil':solPSource_soil,
        'sedPSource_surface':sedPSource_surface,
        'sedPSource_soil':sedPSource_soil,
        'colPSource_surface':colPSource_surface,
        'colPSource_soil':colPSource_soil,

        'solPFlow_surface':solPFlow_surface,
        'colPFlow_surface':colPFlow_surface,
        'sedPFlow_surface':sedPFlow_surface,
        'solPFlow_soil':solPFlow_soil,
        'colPFlow_soil':colPFlow_soil,
        'sedPFlow_soil':sedPFlow_soil,


    }

    # 本月的土壤磷、泥沙产生量，生成sedP、solP、sediment csv文件

    # 进行反向递归+拦截模块，生成sedP、solP、sediment的汇流量


def trans(paraDict,x,y):
    resArr = {
        'runoff': {
            'surface': [],
            'soil': [],
            'total': []
        },
        'sedP': {
            'surface': [],
            'soil': [],
            'total': []
            },
        'solP':{
            'surface': [],
            'soil': [],
            'total': []
        },
        'colP':{
            'surface': [],
            'soil': [],
            'total': []
        },
        'TP':{
            'surface': [],
            'soil': [],
            'total': []
        },
        'sed':{
            'surface':[],
            'soil': [],
            'total':[]
        },
        'col':{
            'surface': [],
            'soil': [],
            'total': []
        }
    }
    sedPList = []
    solPList = []
    sedList = []
    colPlist = []
    colList = []
    TPList = []
    for i in range(1,12):
        rainfall = monthRainfall[i - 1]['rainfall']
        if i == 1:
            res = oneMonthProcess(paraDict, i,{})
            trans = res['runoff_flow'][184][39] * 1000 * 0.09
            trans2 =  0.09 * 1000000 / res['runoff_flow'][184][39]
            pd.DataFrame(res['runoff_flow']).to_csv(
                r'C:\Users\yezouhua\Desktop\master\webPlatform\nineMonth\modelResult\runoff.csv')

            resArr['runoff']['surface'].append(float(res['runoff_flow'][x][y]))
            resArr['runoff']['soil'].append(float(res['runoff_soil_flow'][x][y]))
            resArr['runoff']['total'].append(float(res['runoff_flow'][x][y])+float(res['runoff_soil_flow'][x][y]))
            resArr['solP']['surface'].append(float(res['solPFlow_surface'][x][y]) / trans)
            resArr['solP']['soil'].append(float(res['solPFlow_soil'][x][y]) / trans)
            resArr['solP']['total'].append(float(res['solPFlow_surface'][x][y]+res['solPFlow_soil'][x][y]) / trans)
            resArr['sedP']['surface'].append(float(res['sedPFlow_surface'][x][y]) / trans)
            resArr['sedP']['soil'].append(float(res['sedPFlow_soil'][x][y]) / trans)
            resArr['sedP']['total'].append(float(res['sedPFlow_surface'][x][y]+res['sedPFlow_soil'][x][y]) / trans)
            resArr['colP']['surface'].append(float(res['colPFlow_surface'][x][y]) / trans)
            resArr['colP']['soil'].append(float(res['colPFlow_soil'][x][y]) / trans)
            resArr['colP']['total'].append(float(res['colPFlow_surface'][x][y]+res['colPFlow_soil'][x][y]) / trans)
            #
            # resArr['colP_amount']['surface'].append(float(res['colPFlow_surface'][x][y])  * float(res['runoff_flow'][x][y]) / trans)
            # resArr['colP_amount']['soil'].append(float(res['colPFlow_soil'][x][y]) * float(res['runoff_soil_flow'][x][y]) / trans)
            # resArr['colP_amount']['underground'].append(float(res['colPFlow_underground'][x][y]) * float(res['runoff_groundwater_flow'][x][y]) / trans)
            # resArr['colP_amount']['total'].append(
            #     float(res['colPFlow_surface'][x][y] * res['runoff_flow'][x][y] + res['colPFlow_soil'][x][y] *res['runoff_soil_flow'][x][y]
            #           + res['colPFlow_underground'][x][y] * res['runoff_groundwater_flow'][x][y]) / trans)

            resArr['TP']['surface'].append(float(res['solPFlow_surface'][x][y]+res['sedPFlow_surface'][x][y]+res['colPFlow_surface'][x][y]) / trans)
            resArr['TP']['soil'].append(float(res['solPFlow_soil'][x][y]+res['sedPFlow_soil'][x][y]+res['colPFlow_soil'][x][y]) / trans)
            resArr['TP']['total'].append(float(res['solPFlow_surface'][x][y]+res['sedPFlow_surface'][x][y]+res['colPFlow_surface'][x][y]+
                                               res['solPFlow_soil'][x][y]+res['sedPFlow_soil'][x][y]+res['colPFlow_soil'][x][y]) / trans
                                         )
            # resArr['sed']['surface'].append(float(res['sedFlow'][x][y]) * trans2)
            # resArr['sed']['total'].append(float(res['sedFlow'][x][y]) * trans2)
            # resArr['col']['surface'].append(float(res['colFlow_surface'][x][y]) * trans2)
            # resArr['col']['soil'].append(float(res['colFlow_soil'][x][y]) * trans2)
            # resArr['col']['underground'].append(float(res['colFlow_underground'][x][y]) * trans2)
            # resArr['col']['total'].append(float(res['colFlow_surface'][x][y]+res['colFlow_soil'][x][y]+res['colFlow_underground'][x][y]) * trans2)

        else:
            res = oneMonthProcess(paraDict,i,res)
            if res['runoff_flow'][x][y] == 0:
                resArr['runoff']['surface'].append(0)
                resArr['runoff']['soil'].append(0)
                resArr['runoff']['total'].append(0)
                resArr['solP']['surface'].append(0)
                resArr['solP']['soil'].append(0)
                resArr['solP']['total'].append(0)
                resArr['sedP']['surface'].append(0)
                resArr['sedP']['soil'].append(0)
                resArr['sedP']['total'].append(0)
                resArr['colP']['surface'].append(0)
                resArr['colP']['soil'].append(0)
                resArr['colP']['total'].append(0)
            else:
                trans = res['runoff_flow'][184][39] * 1000 * 0.09
                trans2 = 0.09 * 1000000 / res['runoff_flow'][184][39]
                resArr['runoff']['surface'].append(float(res['runoff_flow'][x][y]))
                resArr['runoff']['soil'].append(float(res['runoff_soil_flow'][x][y]))
                resArr['runoff']['total'].append(float(res['runoff_flow'][x][y]) + float(res['runoff_soil_flow'][x][y]))
                resArr['solP']['surface'].append(float(res['solPFlow_surface'][x][y]) / trans)
                resArr['solP']['soil'].append(float(res['solPFlow_soil'][x][y]) / trans)
                resArr['solP']['total'].append(float(res['solPFlow_surface'][x][y] + res['solPFlow_soil'][x][y]) / trans)
                resArr['sedP']['surface'].append(float(res['sedPFlow_surface'][x][y]) / trans)
                resArr['sedP']['soil'].append(float(res['sedPFlow_soil'][x][y]) / trans)
                resArr['sedP']['total'].append(float(res['sedPFlow_surface'][x][y] + res['sedPFlow_soil'][x][y]) / trans)
                resArr['colP']['surface'].append(float(res['colPFlow_surface'][x][y]) / trans)
                resArr['colP']['soil'].append(float(res['colPFlow_soil'][x][y]) / trans)
                resArr['colP']['total'].append(float(res['colPFlow_surface'][x][y] + res['colPFlow_soil'][x][y]) / trans)

            #
            # resArr['colP_amount']['surface'].append(float(res['colPFlow_surface'][x][y])  * float(res['runoff_flow'][x][y]) / trans)
            # resArr['colP_amount']['soil'].append(float(res['colPFlow_soil'][x][y]) * float(res['runoff_soil_flow'][x][y]) / trans)
            # resArr['colP_amount']['underground'].append(float(res['colPFlow_underground'][x][y]) * float(res['runoff_groundwater_flow'][x][y]) / trans)
            # resArr['colP_amount']['total'].append(
            #     float(res['colPFlow_surface'][x][y] * res['runoff_flow'][x][y] + res['colPFlow_soil'][x][y] *res['runoff_soil_flow'][x][y]
            #           + res['colPFlow_underground'][x][y] * res['runoff_groundwater_flow'][x][y]) / trans)

            resArr['TP']['surface'].append(
                float(res['solPFlow_surface'][x][y] + res['sedPFlow_surface'][x][y] + res['colPFlow_surface'][x][y]) / trans)
            resArr['TP']['soil'].append(
                float(res['solPFlow_soil'][x][y] + res['sedPFlow_soil'][x][y] + res['colPFlow_soil'][x][y]) / trans)
            resArr['TP']['total'].append(
                float(res['solPFlow_surface'][x][y] + res['sedPFlow_surface'][x][y] + res['colPFlow_surface'][x][y] +
                      res['solPFlow_soil'][x][y] + res['sedPFlow_soil'][x][y] + res['colPFlow_soil'][x][y]) / trans
                )
            # resArr['sed']['surface'].append(float(res['sedFlow'][x][y]) * trans2)
            # resArr['sed']['total'].append(float(res['sedFlow'][x][y]) * trans2)
            # resArr['col']['surface'].append(float(res['colFlow_surface'][x][y]) * trans2)
            # resArr['col']['soil'].append(float(res['colFlow_soil'][x][y]) * trans2)
            # resArr['col']['underground'].append(float(res['colFlow_underground'][x][y]) * trans2)
            # resArr['col']['total'].append(float(res['colFlow_surface'][x][y]+res['colFlow_soil'][x][y]+res['colFlow_underground'][x][y]) * trans2)
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
    for i in range(0,len(pre)):
        if math.isnan(pre[i]):
            pre[i] = 0
    if len(obs) > len(pre):
        obs = obs[0:len(pre)]
    elif len(pre) > len(obs):
        pre = pre[0:len(pre)]
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
    for i in range(0,len(pre)):
        if math.isnan(pre[i]):
            pre[i] = 0
    if len(obs) > len(pre):
        obs = obs[0:len(pre)]
    elif len(pre) > len(obs):
        pre = pre[0:len(pre)]

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

def process(
        PSP,RSDIN,SOL_BD,SOL_CBN,CMN,CLAY,SOL_AWC,RSDCO,
        PHOSKD,V_SET,D50,AI2,RHOQ,BC4,RS5,RS2,INTER_SED_PARA_1,
        INTER_SED_PARA_2,INTER_SED_PARA_3,INTER_SED_PARA_4,
        INTER_SED_PARA_5,INTER_COL_PARA_1,INTER_COL_PARA_2,
        INTER_COL_PARA_3,INTER_COL_PARA_4,INTER_COL_PARA_5,
        INTER_SEDP_PARA_1,INTER_SEDP_PARA_2,INTER_SEDP_PARA_3,
        INTER_SEDP_PARA_4,INTER_SEDP_PARA_5,INTER_COLP_PARA_1,
        INTER_COLP_PARA_2,INTER_COLP_PARA_3,INTER_COLP_PARA_4,
        INTER_COLP_PARA_5,INTER_RESP_PARA_1,INTER_RESP_PARA_2,
        INTER_RESP_PARA_3,INTER_RESP_PARA_4,INTER_RESP_PARA_5,
        R0,R1,Q_SURF_K1,Q_SURF_K2,Q_SOIL_K1,PARA_PH0,PARA_PH1,
        PARA_PH2,PARA_PH3,PARA_PH4,CN_sloping,CN_forest,CN_paddy,
        FMINN,FNH3N,FORGN,FMINP,FORGP,defaultCol
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
    for PSP,RSDIN,SOL_BD,SOL_CBN,CMN,CLAY,SOL_AWC,RSDCO, \
        PHOSKD,V_SET,D50,AI2,RHOQ,BC4,RS5,RS2,INTER_SED_PARA_1, \
        INTER_SED_PARA_2,INTER_SED_PARA_3,INTER_SED_PARA_4, \
        INTER_SED_PARA_5,INTER_COL_PARA_1,INTER_COL_PARA_2, \
        INTER_COL_PARA_3,INTER_COL_PARA_4,INTER_COL_PARA_5, \
        INTER_SEDP_PARA_1,INTER_SEDP_PARA_2,INTER_SEDP_PARA_3, \
        INTER_SEDP_PARA_4,INTER_SEDP_PARA_5,INTER_COLP_PARA_1, \
        INTER_COLP_PARA_2,INTER_COLP_PARA_3,INTER_COLP_PARA_4, \
        INTER_COLP_PARA_5,INTER_RESP_PARA_1,INTER_RESP_PARA_2, \
        INTER_RESP_PARA_3,INTER_RESP_PARA_4,INTER_RESP_PARA_5, \
        R0,R1,Q_SURF_K1,Q_SURF_K2,Q_SOIL_K1,PARA_PH0,PARA_PH1, \
        PARA_PH2,PARA_PH3,PARA_PH4,CN_sloping,CN_forest,CN_paddy,\
            FMINN,FNH3N,FORGN,FMINP,FORGP,defaultCol in zip(
        PSP, RSDIN, SOL_BD, SOL_CBN, CMN, CLAY, SOL_AWC, RSDCO,
        PHOSKD, V_SET, D50, AI2, RHOQ, BC4, RS5, RS2, INTER_SED_PARA_1,
        INTER_SED_PARA_2, INTER_SED_PARA_3, INTER_SED_PARA_4,
        INTER_SED_PARA_5, INTER_COL_PARA_1, INTER_COL_PARA_2,
        INTER_COL_PARA_3, INTER_COL_PARA_4, INTER_COL_PARA_5,
        INTER_SEDP_PARA_1, INTER_SEDP_PARA_2, INTER_SEDP_PARA_3,
        INTER_SEDP_PARA_4, INTER_SEDP_PARA_5, INTER_COLP_PARA_1,
        INTER_COLP_PARA_2, INTER_COLP_PARA_3, INTER_COLP_PARA_4,
        INTER_COLP_PARA_5, INTER_RESP_PARA_1, INTER_RESP_PARA_2,
        INTER_RESP_PARA_3, INTER_RESP_PARA_4, INTER_RESP_PARA_5,
        R0, R1, Q_SURF_K1, Q_SURF_K2, Q_SOIL_K1, PARA_PH0, PARA_PH1,
        PARA_PH2, PARA_PH3, PARA_PH4, CN_sloping,CN_forest,CN_paddy,
        FMINN,FNH3N,FORGN,FMINP,FORGP,defaultCol
    ):
        time += 1
        # 一组参数
        paraDict = {
            "PSP":PSP,
            "RSDIN":RSDIN,
            "SOL_BD":SOL_BD,
            "SOL_CBN":SOL_CBN,
            "CMN":CMN,
            "CLAY":CLAY,
            "SOL_AWC":SOL_AWC,
            "RSDCO":RSDCO,
            "PHOSKD":PHOSKD,
            "V_SET":V_SET,
            "D50":D50,
            "AI2":AI2,
            "RHOQ":RHOQ,
            "BC4":BC4,
            "RS5":RS5,
            "RS2":RS2,
            "INTER_SED_PARA_1":INTER_SED_PARA_1,
            "INTER_SED_PARA_2":INTER_SED_PARA_2,
            "INTER_SED_PARA_3":INTER_SED_PARA_3,
            "INTER_SED_PARA_4":INTER_SED_PARA_4,
            "INTER_SED_PARA_5":INTER_SED_PARA_5,
            "INTER_COL_PARA_1":INTER_COL_PARA_1,
            "INTER_COL_PARA_2":INTER_COL_PARA_2,
            "INTER_COL_PARA_3":INTER_COL_PARA_3,
            "INTER_COL_PARA_4":INTER_COL_PARA_4,
            "INTER_COL_PARA_5":INTER_COL_PARA_5,
            "INTER_SEDP_PARA_1":INTER_SEDP_PARA_1,
            "INTER_SEDP_PARA_2":INTER_SEDP_PARA_2,
            "INTER_SEDP_PARA_3":INTER_SEDP_PARA_3,
            "INTER_SEDP_PARA_4":INTER_SEDP_PARA_4,
            "INTER_SEDP_PARA_5":INTER_SEDP_PARA_5,
            "INTER_COLP_PARA_1":INTER_COLP_PARA_1,
            "INTER_COLP_PARA_2":INTER_COLP_PARA_2,
            "INTER_COLP_PARA_3":INTER_COLP_PARA_3,
            "INTER_COLP_PARA_4":INTER_COLP_PARA_4,
            "INTER_COLP_PARA_5":INTER_COLP_PARA_5,
            "INTER_RESP_PARA_1":INTER_RESP_PARA_1,
            "INTER_RESP_PARA_2":INTER_RESP_PARA_2,
            "INTER_RESP_PARA_3":INTER_RESP_PARA_3,
            "INTER_RESP_PARA_4":INTER_RESP_PARA_4,
            "INTER_RESP_PARA_5":INTER_RESP_PARA_5,
            "R0":R0,
            "R1":R1,
            "Q_SURF_K1":Q_SURF_K1,
            "Q_SURF_K2":Q_SURF_K2,
            "Q_SOIL_K1":Q_SOIL_K1,
            "PARA_PH0":PARA_PH0,
            "PARA_PH1":PARA_PH1,
            "PARA_PH2":PARA_PH2,
            "PARA_PH3":PARA_PH3,
            "PARA_PH4":PARA_PH4,
            "CN_sloping":CN_sloping,
            "CN_forest":CN_forest,
            "CN_paddy":CN_paddy,
            "FMINN":FMINN,
            "FNH3N":FNH3N,
            "FORGN":FORGN,
            "FMINP":FMINP,
            "FORGP":FORGP,
            "defaultCol":defaultCol
        }
        paraRes.append(paraDict)
        # 关键传输函数，返回一整次模拟的所有结果
        res = trans(paraDict, 209, 44)

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
            n_var=60,
            n_obj=len(celibratedTarget)*3,
            xl=anp.array(
                [
                    0.01,
                    0,
                    0.9,
                    0.05,
                    0.001,
                    0,
                    0,
                    0.02,
                    100,
                    0,
                    10,
                    0.01,
                    0.05,
                    0.01,
                    0.001,
                    0.001,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    -5,
                    0,
                    100,
                    0,
                    0,
                    0,
                    -14000,
                    8000,
                    -3000,
                    200,
                    -10,
                    50, # CN_sloping
                    50, # CN_forest
                    50, # CN_paddy
                    0,
                    0,
                    0,
                    0,
                    0,
                    0

                ]),  # 变量下界
            xu=anp.array(
                [0.7,
                  10000,
                  2.5,
                  10,
                  0.003,
                  100,
                  1,
                  0.1,
                  200,
                  100,
                  100,
                  0.02,
                  0.5,
                  0.7,
                  0.01,
                  0.1,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  5,
                  100,
                  300,
                  300,
                  300,
                  300,
                 -12000,
                 12000,
                 -2000,
                 300,
                 -8,
                  100, # CN_sloping
                  100, # CN_forest
                  100, # CN_paddy
                 0.5,
                 0.5,
                 0.5,
                 0.5,
                 0.5,
                 5
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
                     x[:, 49], x[:, 50],x[:, 51], x[:, 52],x[:, 53],
                     x[:, 54], x[:, 55], x[:, 56], x[:, 57], x[:, 58],x[:, 59],
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
print('res.X', res.X)
print('res.F', res.F)  # 显示结果
