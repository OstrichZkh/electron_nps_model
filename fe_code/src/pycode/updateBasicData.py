import sys
import json
import datetime
import calendar
import os
from osgeo import gdal
import numpy as np
import pandas as pd
# os.system('chcp 65001')
# type = sys.argv[1]
# filePath = sys.argv[2]
# jsonPath = sys.argv[3]
# projectName = sys.argv[4]
# projectName = filePath.split('\\')[-1]

type = 'landuse'
filePath = r'E:\webplatform\exp1'
jsonPath = r'E:\webplatform\fe_code\projectInfo.json'
os.environ['PROJ_LIB'] = r'C:\Users\yezouhua\AppData\Local\Programs\Python\Python39\Lib\site-packages\pyproj\proj_dir\share\proj'
projectName = filePath.split('\\')[-1]

try:
    if type == 'rainfall':

        rainfallPath = filePath + r'\database\rainfall.txt'
        # filePath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo'
        # jsonPath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo\dataInfo.json'
        # rainfallPath = r'C:\Users\yezouhua\Desktop\master\webPlatform\newdemo\rain.txt'
        # 获取降雨列表
        rainfallArr = []
        for line in open(rainfallPath):
            rainfallArr.append(line.replace('\n',''))
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

        startDateTime = datetime.date(int(startDate[0]),int(startDate[1]),int(startDate[2]))
        endDateTime = datetime.date(int(endDate[0]),int(endDate[1]),int(endDate[2]))
        gapDays = (endDateTime-startDateTime).days+1
        gapYears = float((endDateTime-startDateTime).days/365)


        monthSum = 0
        monthArr = []
        count = 0
        dateArr = []
        while True:
            # 最后一天了
            monthSum += float(rainfallArr[count])
            count = count + 1
            monBefore = startDateTime.month
            startDateTime = startDateTime+datetime.timedelta(days=1)
            monAfter = startDateTime.month
            # 到了下一个月了
            if(monBefore!=monAfter or count==len(rainfallArr)):
                if(monthSum>=0):
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
        temp = 0 #计算a、b因子的临时list
        count = 0
        for rainfall in rainfallArr:
            if float(rainfall) > 12:
                temp+=float(rainfall)
                count+=1
        Pd12 = temp/count
        Py12 = temp/gapYears
        b = 0.8363 + 18.177/Pd12 + 24.455/Py12
        a = 21.589*b**(-7.1891)
        file = open(filePath + r'\R_factor.txt','w')
        for rainfall in rainfallArr_R:
            R = a*float(rainfall)**b
            file.write(str(R))
            file.write('\n')
        # 发送给主进程降雨数据
        monthList = []
        curY = int(startDate[0])
        curM = int(startDate[1])
        endY = int(endDate[0])
        endM = int(endDate[1])
        while curY < endY or (curY == endY and curM <= endM):
            monthList.append(str(curY)+'/' + str(curM))
            if curM == 12:
                curM = 1
                curY += 1
            else:
                curM += 1
        rainfallList = []
        for i in range(0,len(monthList)):
            rainfallList.append({
                'date':monthList[i],
                'rainfall':monthArr[i]
            })
        print(rainfallList)
    elif type == 'landuse':
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
        sourcePath = filePath + r'\database\landuse.tif'
        data2 = load_img_to_array(sourcePath)
        output2 = pd.DataFrame(data2)
        output2.to_csv(filePath + r'\database\landuse.csv')
        luDF = pd.read_csv(filePath + r'\database\landuse.csv', index_col=0).values
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
except:
    print('err')
