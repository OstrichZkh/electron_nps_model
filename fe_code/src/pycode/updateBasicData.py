import sys
import json
import datetime
import calendar
# os.system('chcp 65001')
filePath = sys.argv[1]
jsonPath = sys.argv[2]
# filePath = r'E:\webplatform\project_example4'
# jsonPath = r'E:\webplatform\fe_code\projectInfo.json'
try:

    rainfallPath = filePath + r'\rainfall.txt'

    #
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
except:
    print('err')
