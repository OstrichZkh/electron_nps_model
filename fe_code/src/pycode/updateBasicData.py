import sys
import json
import datetime
import calendar
import os
from osgeo import gdal
import numpy as np
import pandas as pd
from copy import deepcopy
# os.system('chcp 65001')
os.environ['PROJ_LIB'] = r'C:\Users\yezouhua\AppData\Local\Programs\Python\Python39\Lib\site-packages\pyproj\proj_dir\share\proj'

type = sys.argv[1]
filePath = sys.argv[2]
jsonPath = sys.argv[3]
# projectName = sys.argv[4]
#
# type = 'landuse'
# filePath = r'E:\webplatform\asd'
# jsonPath = r'E:\webplatform\fe_code\projectInfo.json'
projectName = filePath.split('\\')[-1]


def load_img_to_array(img_file_path):
    dataset = gdal.Open(img_file_path)  # 读取栅格数据
    Bands = np.array([dataset.RasterCount])
    # 判断是否读取到数据
    if dataset is None:
        sys.exit(1)  # 退出
    projection = dataset.GetProjection()  # 投影
    transform = dataset.GetGeoTransform()  # 几何信息
    array_channel = 0  # 数组从通道从0开始

    # 读取Bands列表中指定的波段
    for band in Bands:  # 图片波段从1开始
        band = int(band)
        srcband = dataset.GetRasterBand(band)  # 获取栅格数据集的波段
        if srcband is None:
            continue
        #  一个通道转成一个数组（5888,5888）
        arr = srcband.ReadAsArray()
    return arr


def cellaround(x, y, data):
    xaround = np.zeros((8, 1))
    xaround[0] = data[x + 1, y]  # 右
    xaround[1] = data[x + 1, y + 1]  # 右下
    xaround[2] = data[x, y + 1]  # 下
    xaround[3] = data[x - 1, y + 1]  # 左下
    xaround[4] = data[x - 1, y]  # 左
    xaround[5] = data[x - 1, y - 1]  # 左上
    xaround[6] = data[x, y - 1]  # 上
    xaround[7] = data[x + 1, y - 1]  # 右上
    return xaround


def sinkcount(data):
    nrow, ncol = data.shape
    nodata = np.min(data)
    sinkcount = 0
    for i in range(1, nrow - 1):
        for j in range(1, ncol - 1):
            x = data[i, j]
            if x != nodata:
                if ((cellaround(i, j, data) - x) > 0).all() == 1:
                    sinkcount += 1
    return sinkcount


def sinkfill(data, zlimit):
    """
    fill: 填洼
    zlimit: 允许的最大坡降值
    """
    nrow, ncol = data.shape
    nodata = np.min(data)
    for i in range(1, nrow - 1):
        for j in range(1, ncol - 1):
            x = data[i, j]
            if x != nodata:
                if ((cellaround(i, j, data) - x) > zlimit).all() == 1:
                    data[i, j] = np.min(cellaround(i, j, data))
    return data


try:
    if type == 'rainfall':

        rainfallPath = filePath + r'\database\rainfall.txt'
        # filePath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo'
        # jsonPath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo\dataInfo.json'
        # rainfallPath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo\rain.txt'
        # 获取降雨列表
        rainfallArr = []
        for line in open(rainfallPath):
            rainfallArr.append(line.replace('\n', ''))
        # 此文件用于计算降雨数据
        rainfallArr.pop(0)

        # 读取项目的起始，结束时间
        # with open(jsonPath, "r") as f:
        #     projInfo = json.load(f)

        js = open(jsonPath)
        projInfo = json.load(js)[0]
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
        with open(filePath + r'\database\R_factor.txt', 'w') as json_file:
            json_file.write(json_str)
        print(rainfallList)
    elif type == 'landuse':

        sourcePath = filePath + r'\database\landuse.tif'
        data2 = load_img_to_array(sourcePath)
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\landuse.csv')
        luDF = pd.read_csv(filePath + r'\database\landuse.csv', index_col=0).values
        with open(jsonPath, "r", encoding="utf-8") as f:
            infos = json.load(f)
        targetInfo = {}
        for info in infos:
            if info["projectName"] == projectName:
                targetInfo = info
        P_factor_DF_10000times = deepcopy(luDF)
        res = 0
        luDict = {}
        for x in range(0, len(luDF)):
            for y in range(0, len(luDF[0])):
                if luDF[x][y] > -1000:
                    res += 1
                code = luDF[x][y]
                if str(code) in luDict:
                    luDict[str(code)] += 1
                else:
                    luDict[str(code)] = 1
                for c in targetInfo['landUse']['code']:
                    if code == c['code']:
                        type == c['type']
                        if type == 'forest':
                            P_factor_DF_10000times[x][y] = 0.9 * 10000
                        elif type == 'paddy':
                            P_factor_DF_10000times[x][y] = 0.25 * 10000
                        elif type == 'sloping':
                            P_factor_DF_10000times[x][y] = 0.35 * 10000
                        elif type == 'construct':
                            P_factor_DF_10000times[x][y] = 1 * 10000
                        elif type == 'water':
                            P_factor_DF_10000times[x][y] = 0

        projInfo = json.load(open(jsonPath))
        pd.DataFrame(P_factor_DF_10000times).to_csv(filePath + r'\database\P_factor_10000times.csv')
        print(json.dumps(luDict))
    elif type == 'soiltype':
        sourcePath = filePath + r'\database\soiltype.tif'
        data2 = load_img_to_array(sourcePath)
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\soiltype.csv')
        luDF = pd.read_csv(filePath + r'\database\soiltype.csv', index_col=0).values
        res = 0
        luDict = {}
        for x in range(0, len(luDF)):
            for y in range(0, len(luDF[0])):
                if luDF[x][y] > -1000:
                    res += 1
                code = luDF[x][y]
                if str(code) in luDict:
                    luDict[str(code)] += 1
                else:
                    luDict[str(code)] = 1
        projInfo = json.load(open(jsonPath))
        print(json.dumps(luDict))
        with open(jsonPath, "r", encoding="utf-8") as f:
            infos = json.load(f)
        targetInfo = {}
        for info in infos:
            if info["projectName"] == projectName:
                targetInfo = info
        K_factor_DF = deepcopy(luDF)
        for x in range(0, len(K_factor_DF)):
            for y in range(0, len(K_factor_DF[0])):
                code = K_factor_DF[x][y]
                if code >0 and code < 20:
                    for c in targetInfo['soiltype']['code']:
                        if code == c['code']:
                            K_factor_DF[x][y] = c['kValue']*10000
                else:
                    K_factor_DF[x][y] = -1

        pd.DataFrame(K_factor_DF).to_csv(filePath + r'\database\K_factor_10000times.csv')

    elif type == 'DEM':
        sourcePath = filePath + r'\database\DEM.tif'
        data2 = load_img_to_array(sourcePath)
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\DEM.csv')
        DEMDF = pd.read_csv(filePath + r'\database\DEM.csv', index_col=0).values
        res = 0
        DEMArr = []
        for x in range(0, len(DEMDF)):
            for y in range(0, len(DEMDF[0])):
                dem = DEMDF[x][y]
                if dem > 0 and dem < 8000:
                    DEMArr.append(dem)
        DEMArr.sort()
        minDEM = DEMArr[0]
        maxDEM = DEMArr[len(DEMArr) - 1]
        gap = (maxDEM - minDEM) / 10
        countArr = []
        demArr = []
        for i in range(1, 11):
            nextMax = gap * i + minDEM

            demArr.append('%s-%s' % (int(nextMax - gap), int(nextMax)))
            count = 0
            while DEMArr.pop(0) < nextMax:
                count += 1
            countArr.append(count)
        print(json.dumps({
            'DEM': demArr,
            'count': countArr
        }))
    elif type == 'C_factor' or type == 'L_factor' or type == 'S_factor':
        sourcePath = filePath + r'\database\{}.tif'.format(type)
        data2 = load_img_to_array(sourcePath)
        for x in range(0,len(data2)):
            for y in range(0,len(data2[0])):
                val = data2[x][y]
                if val >=0 or val <= 10000000:
                    data2[x][y] = val * 10000
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\{}_10000times.csv'.format(type))
        print('ok')
    elif type =='D8' or type == 'slope':
        sourcePath = filePath + r'\database\{}.tif'.format(type)
        data2 = load_img_to_array(sourcePath)
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\{}.csv'.format(type))
        print('ok')
    elif type == "rusleCal":
        with open(filePath + r'\database\R_factor.txt', "r", encoding="utf-8") as f:
            rusleDict = json.load(f)

        K_factor = pd.read_csv(filePath + r'\database\K_factor_10000times.csv',index_col=0).values
        C_factor = pd.read_csv(filePath + r'\database\C_factor_10000times.csv',index_col=0).values
        L_factor = pd.read_csv(filePath + r'\database\L_factor_10000times.csv',index_col=0).values
        S_factor = pd.read_csv(filePath + r'\database\S_factor_10000times.csv',index_col=0).values
        P_factor = pd.read_csv(filePath + r'\database\P_factor_10000times.csv',index_col=0).values


        X1 = len(K_factor)
        X2 = len(C_factor)
        X3 = len(L_factor)
        X4 = len(S_factor)

        Y1 = len(K_factor[0])
        Y2 = len(C_factor[0])
        Y3 = len(L_factor[0])
        Y4 = len(S_factor[0])

        if X1 == X2 and X2 == X3 and X3 == X4 and Y1 == Y2 and Y2 == Y3 and Y3==Y4:
            cnt = 0
            for i in range(0,len(rusleDict)):
                # 一个月的运算过程
                oneMonthRusleDf = deepcopy(K_factor)
                year = rusleDict[i]['date'].split('/')[0]
                month = rusleDict[i]['date'].split('/')[1]
                r = rusleDict[i]['R_factor']
                oneMonthRusleSum = 0
                for x in range(0,X1):
                    for y in range(0,Y1):
                        k = K_factor[x][y] / 10000
                        c = C_factor[x][y] / 10000
                        l = L_factor[x][y] / 10000
                        s = S_factor[x][y] / 10000
                        p = P_factor[x][y] / 10000
                        if k > 0 and k < 10000:
                            oneMonthRusleSum += r*k*c*l*s
                            oneMonthRusleDf[x][y] = r*k*c*l*s
                        else:
                            oneMonthRusleDf[x][y] = -1
                if not os.path.exists(r"{}\rusle".format(filePath)):
                    os.mkdir(r"{}\rusle".format(filePath))
                cnt += 1
                path = r"{}\rusle\{}_{}_{}.csv".format(filePath,year,month,cnt)
                pd.DataFrame(oneMonthRusleDf).to_csv(path)
                rusleDict[i]['rusle'] = oneMonthRusleSum
            with open(filePath + r'\database\R_factor.txt', 'w',encoding="utf-8") as fp:
                json.dump(rusleDict, fp)
            print('done')
        else:
            print('unmatch')




except:
    print('err')
