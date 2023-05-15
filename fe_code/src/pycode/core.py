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
# projectFile = sys.argv[1]
# jsonPath = sys.argv[2]

projectFile = r'E:\webplatform\asd'
jsonPath = r'E:\webplatform\fe_code\projectInfo.json'
projectName = projectFile.split('\\')[-1]
fileList = os.listdir(projectFile+r'\observeData')
# 清空率定数据
os.remove(projectFile + r'\calibrateResult.json')
# 施肥措施数据
allProjectInfo = []
with open(jsonPath,'r',encoding='utf-8') as fp:
    allProjectInfo = json.load(fp)
curProjectInfo = list(filter(lambda info: info["projectName"] == projectName,allProjectInfo))[0]
# 获取率定目标及观测值
[celibratedTarget,celibratedValue] = utils.getCelibrateData(curProjectInfo,projectFile)

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
[landuseDict,forestCode,slopelandCode,paddylandCode,waterCode,buildingCode] = utils.getLanduseCode(curProjectInfo)
landuseDictDemo = {'1': 'forest',
 '2': 'sloping',
 '3': 'water',
 '4': 'paddy',
 '5': 'construct'}
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
    # 地表径流、壤中流产汇流模块
    rainfall = monthRainfall[month - 1]['rainfall']
    [
        runoff_generate,
        runoff_soil_generate,
        runoff_flow,
        runoff_soil_flow
    ] = utils.hydroModule(rainfall,paraDict,landuseDF)
    pd.DataFrame(runoff_generate).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\地表径流_产生量.csv')
    pd.DataFrame(runoff_soil_generate).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\壤中流_产生量.csv')
    pd.DataFrame(runoff_flow).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\地表径流_汇流量.csv')
    pd.DataFrame(runoff_soil_flow).to_csv(projectFile+r'\modelResult\month'+str(month)+r'\壤中流_汇流量.csv')

    # 本月的土壤磷循环、施肥措施，生成六个不同的soilP.csv文件
    # 初始化参数
    # 土壤温度
    [
        minP_act,
        minP_sta,
        orgP_hum,
        orgP_frsh,
        orgP_act,
        orgP_sta,
        P_solution,
        NO3,
        orgN_hum,
        orgN_act,
        orgN_sta,
        orgN_frsh,
    ] =    utils.soilProcess(month,preMonthResult)
    # 胶体计算
    [
        colSource_surface,
        colSource_soil
    ] = utils.colProcess(phDict,rusle)
    # 污染源计算，获得solPSource，sedPSource两个DF
    [
        solPSource_soil,
        solPSource_surface,
        sedPSource_soil,
        sedPSource_surface,
        colPSource_soil,
        colPSource_surface
    ] = utils.pollutionSourceProcess(rusle)
    # 污染传输过程
    [
        solPFlow_surface,
        colPFlow_surface,
        sedPFlow_surface,
        solPFlow_soil,
        colPFlow_soil,
        sedPFlow_soil,
    ] = utils.pollutionTranslateProcess(slopeDF,C_factorDF)

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
                trans = res['runoff_flow'][x][y] * 1000 * 0.09
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
    if fenMu == 0:
        fenMu = 9999999999999999
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
    if fenMu == 0:
        return 0
    print(key,'nse', (1 - fenZi / fenMu),obs,pre)
    return -(1 - fenZi / fenMu)

def RE(obs, pre,key):
    re = 0
    if len(obs) > len(pre):
        Len = len(pre)
    else:
        Len = len(obs)
    for i in range(0, Len):
        re += abs((pre[i]-obs[i]) / obs[i])
    print(key,'RE',re / Len,obs,pre )
    return -re / Len

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
    times = 0
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
        times += 1
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
        resDict = {}
        for key in celibratedTarget:
            r2_ = r2(celibratedValue[key], res[key]['total'],key)
            nse_ = NSE(celibratedValue[key], res[key]['total'],key)
            re_ = RE(celibratedValue[key], res[key]['total'],key)
            objective[key]['r2'].append(r2_)
            objective[key]['nse'].append(nse_)
            objective[key]['re'].append(re_)
            resDict[key] = {
                "r2":r2_,
                "nse":nse_,
                "re_":re_,
                "obs":celibratedValue[key],
                "pre":res[key]['total']
            }
        for k in resDict:
            for key in resDict[k]:
                target = resDict[k][key]
                if isinstance(target,list):
                    newTarget = []
                    for val in target:
                        newTarget.append(str(val))
                else:
                    newTarget = str(target)
                resDict[k][key] = newTarget
        path = projectFile + r'\calibrateResult.json'
        if os.path.exists(path):
            with open(path, 'r') as load_f:
                load_dict = json.load(load_f)
                load_dict[str(time.time())] = resDict
                f = open(path, 'w')
                f.write(json.dumps(load_dict))
                f.close()
        else:
            f = open(path, 'w')
            newDict = {
                str(time.time()):resDict
            }
            f.write(json.dumps(newDict))
            f.close()


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
