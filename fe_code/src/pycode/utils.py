import json

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

def checkAreaMatch(dataframes,names):
    X = len(dataframes[0])
    Y = len(dataframes[0][0])
    for i in range(0,len(dataframes)):
        df = dataframes[0]
        if len(df) != X:
            raise ValueError('{}的dataframe的X值不匹配！'.format(names[i]))
        elif len(df[0]) != Y:
            raise ValueError('{}的dataframe的Y值不匹配！'.format(names[i]))
    return [X,Y]