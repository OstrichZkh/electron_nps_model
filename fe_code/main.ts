// // Modules to control application life and create native browser window
// const { app, BrowserWindow, ipcMain, dialog } = require("electron");
// const path = require("path");

// // Keep a global reference of the window object, if you don't, the window will
// // be closed automatically when the JavaScript object is garbage collected.
// let mainWindow = null;

// function createWindow() {
//   // Create the browser window.
//   mainWindow = new BrowserWindow({
//     width: 900,
//     height: 600,
//     // transparent: true, // 透明窗口
//     opacity: 1, // 全局透明度
//     frame: true, // 隐藏所有操作栏
//     webPreferences: {
//       // 起用预加载文件，此文件可以使用node以及访问其余目录
//       preload: path.join(__dirname, "render.ts"),
//     },
//   });
//   // and load the index.html of the app.

//   // 打包时使用
//   // mainWindow.loadFile('./build/index.html')

//   // 本地调试时使用
//   mainWindow.loadURL("http://localhost:3000/");

//   // Open the DevTools.
//   // mainWindow.webContents.openDevTools()

//   // Emitted when the window is closed.
//   mainWindow.on("closed", function () {
//     // Dereference the window object, usually you would store windows
//     // in an array if your app supports multi windows, this is the time
//     // when you should delete the corresponding element.
//     mainWindow = null;
//   });

//   ipcMain.on('create-new-project', createNewProject)

// }

// // This method will be called when Electron has finished
// // initialization and is ready to create browser windows.
// // Some APIs can only be used after this event occurs.
// app.on("ready", createWindow);

// // Quit when all windows are closed.
// app.on("window-all-closed", function () {
//   // On macOS it is common for applications and their menu bar
//   // to stay active until the user quits explicitly with Cmd + Q
//   if (process.platform !== "darwin") app.quit();
// });

// app.on("activate", function () {
//   // On macOS it's common to re-create a window in the app when the
//   // dock icon is clicked and there are no other windows open.
//   if (mainWindow === null) createWindow();
// });
// // In this file you can include the rest of your app's specific main process
// // code. You can also put them in separate files and require them here.
// async function createNewProject() {
//   const { canceled, filePaths } = await dialog.showOpenDialog()

//   if (canceled) {
//     return
//   } else {
//     return filePaths[0]
//   }
// }

// app.whenReady().then(() => {
//   createWindow()
//   app.on('activate', function () {
//     if (BrowserWindow.getAllWindows().length === 0) createWindow()
//   })
// })



const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const dayjs = require('dayjs');
let projectInfoJson = path.join(__dirname, './projectInfo.json')
let curProjectInfo
let curProjectPath
const spawn = require('child_process').spawn



async function createNewProject() {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    title: '请选择项目位置',       // 对话框的标题
    defaultPath: '',       // 默认的文件名字
    filters: [
      {
        name: '',
        extensions: ['']
      }
    ],
    properties: ['openDirectory'],
    buttonLabel: '选择'     // 自定义按钮文本显示内容
  })
  if (canceled) {
    return
  } else {
    let ProjectPath = filePaths[0]
    let files = fs.readdirSync(ProjectPath)
    if (files.length !== 0) {
      dialog.showMessageBox({
        type: 'warning',
        title: '您选择的文件夹有误',
        message: '请选择空文件夹作为项目目录！',
      })
    } else {
      let projectName = ProjectPath.split('\\')[ProjectPath.split('\\').length - 1]
      let projectInfo = {
        projectName: projectName,
        projectPath: ProjectPath,
        lastSaved: dayjs(new Date).format('YYYY-MM-DD HH:mm:ss'),
        lastSavedStamp: +new Date(),
        area: '0.00 ha',
        periods: {
          startDate: '',
          endDate: ''
        },
        rainfall: {
          state: false
        },
        landUse: {
          state: false,
          grids: 0,
        },
        soiltype: {
          state: false,
          grids: 0,
        },
        DEM: {
          state: false,
          grids: 0,
        },
        D8: {
          state: false,
          grids: 0,
        },
        rusle: {
          S_factor: false,
          C_factor: false,
          L_factor: false,
        },
        slope: {
          state: false,
          grids: 0,
        },
        observeData: {
          TP: {
            checked: false,
            imported: false
          },
          sedP: {
            checked: false,
            imported: false
          },
          solP: {
            checked: false,
            imported: false
          },
          sed: {
            checked: false,
            imported: false
          },
          colP: {
            checked: false,
            imported: false
          },
          col: {
            checked: false,
            imported: false
          }
        }
      }
      curProjectInfo = projectInfo
      curProjectPath = ProjectPath
      let prjectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
      prjectInfos = [projectInfo, ...prjectInfos]
      fs.writeFileSync(projectInfoJson, JSON.stringify(prjectInfos))
      fs.mkdirSync(path.join(ProjectPath, 'database'))
    }
    return ProjectPath
  }
}
function deleteDir(url) {
  var files = [];
  if (fs.existsSync(url)) {  //判断给定的路径是否存在
    files = fs.readdirSync(url);   //返回文件和子目录的数组
    files.forEach(function (file, index) {
      var curPath = path.join(url, file);
      if (fs.statSync(curPath).isDirectory()) { //同步读取文件夹文件，如果是文件夹，则函数回调
        deleteDir(curPath);
      } else {
        fs.unlinkSync(curPath);    //是指定文件，则删除
      }
    });
    fs.rmdirSync(url); //清除文件夹
  } else {
    console.log("给定的路径不存在！");
  }

}

function checkJson() { }
// 更新项目某一信息
function updateStatus(payload) {
  function updateSingleStatus(payload, projectInfo) {
    let { target, value } = payload
    let newObj = projectInfo
    for (let i = 0; i < target.length; i++) {
      let key = target[i]
      if (i == target.length - 1) {
        newObj[key] = value
      } else {
        newObj = newObj[key]
      }
    }
    return projectInfo
  }
  if (Array.isArray(payload)) {
    let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
    let restProjects = projectInfos.filter((info) => info.projectName !== curProjectInfo.projectName)
    for (let practice of payload) {
      curProjectInfo = updateSingleStatus(practice, curProjectInfo)
    }
    fs.writeFileSync(projectInfoJson, JSON.stringify([curProjectInfo, ...restProjects]))
    return curProjectInfo
  } else {
    let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
    let curProject = projectInfos.filter((info) => info.projectName === payload.projectName)[0]
    let restProjects = projectInfos.filter((info) => info.projectName !== payload.projectName)
    for (let practice of payload.payload) {
      curProject = updateSingleStatus(practice, curProject)
    }
    fs.writeFileSync(projectInfoJson, JSON.stringify([curProject, ...restProjects]))
    return curProject
  }

}

function updataStatusWithEntireInfo(info) {
  let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
  let newProjectInfos = [info, ...projectInfos.filter((i) => {
    return i.projectName !== info.projectName
  })]
  fs.writeFileSync(projectInfoJson, JSON.stringify(newProjectInfos))
}
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 2000,
    height: 2000,
    webPreferences: {
      preload: path.join(__dirname, 'render.ts')
    }
  })
  mainWindow.loadURL("http://localhost:3000/");
  mainWindow.webContents.openDevTools({
    mode: 'right'
  });

  // 检查项目JSON文件是否存在，若存在则返回所有项目的信息。
  if (!fs.existsSync(projectInfoJson)) {
    fs.writeFileSync(projectInfoJson, JSON.stringify([]))
  }
  ipcMain.handle('requireProjectInfo', () => {
    let data = JSON.parse(fs.readFileSync(projectInfoJson))
    if (data && data.length) {
      curProjectInfo = data[0]
      curProjectPath = curProjectInfo.projectPath
      return data
    }

  })
  ipcMain.handle('createNewProject', createNewProject)
  ipcMain.handle('deleteProject', (e, payload) => {
    let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
    let newProjectInfos = projectInfos.filter((info) => info.projectName !== payload)
    fs.writeFileSync(projectInfoJson, JSON.stringify(newProjectInfos))
    // 删除项目文件夹
    let path = projectInfos.filter((info) => info.projectName === payload)[0].projectPath
    deleteDir(path)
    console.log(`项目${payload}删除成功`, path);
    return {
      status: 200,
      msg: 'ok'
    }
  })
  ipcMain.handle('updateProjectInfo', (e, payload) => {
    // let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
    if (!payload) {
      return curProjectInfo
    }
    let updatedInfo = updateStatus(payload)
    curProjectInfo = updatedInfo
    return updatedInfo
  })
  ipcMain.handle('uploadFile', (e, payload) => {
    const { filePath, type } = payload
    let pyPath = './src/pycode/updateBasicData.py'
    // 回调函数的返回值不能作为外层函数的返回值，需要再包裹一层Promise
    return new Promise((resolve, reject) => {
      if (payload.type == 'rainfall') {
        // 导入降雨数据并进行统计
        fs.copyFileSync(filePath, path.join(curProjectPath, 'database', 'rainfall.txt'))
        const py = spawn('python', [pyPath, 'rainfall', curProjectPath, path.join(__dirname, './projectInfo.json')])
        py.stdout.on('data', function (rainfallInfo) {
          console.log(rainfallInfo.toString().substr(0, 3), rainfallInfo.toString().substr(0, 3) == 'err');
          if (rainfallInfo == 'err' || rainfallInfo.toString().substr(0, 3) == 'err') {
            reject({
              status: 400,
              msg: 'rainfallErr'
            })
          } else {
            updateStatus([
              { target: ['rainfall', 'value'], value: rainfallInfo.toString().replace(/'/g, '"') },
              { target: ['rainfall', 'state'], value: true }
            ])
            resolve({
              status: 200,
              msg: curProjectInfo
            })
          }

        })

      } else if (payload.type == 'landuse') {
        fs.copyFileSync(filePath, path.join(curProjectPath, 'database', 'landuse.tif'))
        const py = spawn('python', [pyPath, 'landuse', curProjectPath, path.join(__dirname, './projectInfo.json')])
        py.stdout.on('data', function (dict) {
          if (dict.toString() == 'err') {
            reject({
              status: 400,
              msg: 'error'
            })
          }
          curProjectInfo.landUse.state = true
          curProjectInfo.landUse.counts = JSON.parse(dict.toString())
          updataStatusWithEntireInfo(curProjectInfo)

          resolve({
            status: 200,
            msg: curProjectInfo
          })
        })
      } else if (payload.type == 'soiltype') {
        fs.copyFileSync(filePath, path.join(curProjectPath, 'database', 'soiltype.tif'))
        const py = spawn('python', [pyPath, 'soiltype', curProjectPath, path.join(__dirname, './projectInfo.json')])
        py.stdout.on('data', function (dict) {
          if (dict.toString() == 'err') {
            reject({
              status: 400,
              msg: 'error'
            })
          }
          curProjectInfo.soiltype.state = true
          curProjectInfo.soiltype.counts = JSON.parse(dict.toString())
          updataStatusWithEntireInfo(curProjectInfo)
          resolve({
            status: 200,
            msg: curProjectInfo
          })
        })
      } else if (payload.type == 'DEM') {
        fs.copyFileSync(filePath, path.join(curProjectPath, 'database', 'soiltype.tif'))
        const py = spawn('python', [pyPath, 'DEM', curProjectPath, path.join(__dirname, './projectInfo.json')])
        py.stdout.on('data', function (dict) {
          if (dict.toString() == 'err') {
            reject({
              status: 400,
              msg: 'error'
            })
          }
          curProjectInfo.DEM.state = true
          curProjectInfo.DEM.counts = JSON.parse(dict.toString())
          updataStatusWithEntireInfo(curProjectInfo)
          resolve({
            status: 200,
            msg: curProjectInfo
          })
        })
      } else if (['C_factor', 'L_factor', 'S_factor', 'D8', 'slope'].indexOf(payload.type) !== -1) {
        fs.copyFileSync(filePath, path.join(curProjectPath, 'database', `${payload.type}.tif`))
        const py = spawn('python', [pyPath, payload.type, curProjectPath, path.join(__dirname, './projectInfo.json')])
        py.stdout.on('data', function (dict) {
          if (dict.toString() == 'err') {
            reject({
              status: 400,
              msg: 'error'
            })
          }
          if (['C_factor', 'L_factor', 'S_factor'].indexOf(payload.type) !== -1) {
            curProjectInfo.rusle[payload.type] = true
            updataStatusWithEntireInfo(curProjectInfo)
            resolve({
              status: 200,
              msg: curProjectInfo
            })
          } else {
            curProjectInfo[payload.type].state = true
            updataStatusWithEntireInfo(curProjectInfo)
            resolve({
              status: 200,
              msg: curProjectInfo
            })
          }

        })
      } else if (['sed', 'col', 'sedP', 'colP', 'solP', 'TP',].indexOf(payload.type) !== -1) {
        if (!fs.existsSync(path.join(curProjectPath, 'observeData'))) {
          fs.mkdirSync(path.join(curProjectPath, 'observeData'));
        }
        fs.copyFileSync(filePath, path.join(curProjectPath, 'observeData', `${payload.type}.txt`))
        resolve({
          status: 200,
          msg: curProjectInfo
        })
      }
      else {
        reject({
          status: 400,
          msg: 'rainfallErr'
        }
        )
      }
    })

  })
  ipcMain.handle('rusleCal', (e, payload) => {
    let pyPath = './src/pycode/updateBasicData.py'
    return new Promise((resolve, reject) => {
      const py = spawn('python', [pyPath, 'rusleCal', curProjectPath, path.join(__dirname, './projectInfo.json')])
      py.stdout.on('data', function (data) {
        if (data.toString() == 'unmatch') {
          resolve('unmatch')
        } else if (data.toString() == 'err') {
          resolve('err')
        } else {
          resolve('done')
        }
      })

    })
  })
  ipcMain.handle('requireRusle', (e, payload) => {
    try {
      let info = fs.readFileSync(path.join(curProjectPath, 'database', 'R_factor.txt'))
      return JSON.parse(info)
    } catch {
      console.log('err');
      return 'err'
    }
  })
  ipcMain.handle('requireParas', requireParas)
  ipcMain.handle('updateParas', (e, payload) => {
    fs.writeFileSync(path.join(curProjectPath, 'parasInfo.json'), JSON.stringify(payload))
  })
  ipcMain.handle('deleteFile', (e, payload) => {
    return new Promise((resolve, reject) => {
      const dir = path.join(curProjectPath, 'observeData', `${payload.type}.txt`)
      fs.unlink(dir, (err) => {
        if (err) {
          reject({
            status: 400,
            msg: '删除失败'
          })
        }
        resolve(
          {
            status: 200,
            msg: '删除成功'
          }
        )
      })
    })

  })

}
app.whenReady().then(() => {
  createWindow()
  checkJson()
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})

function requireParas(e, payload) {
  if (fs.existsSync(path.join(curProjectPath, 'parasInfo.json'))) {
    return JSON.parse(fs.readFileSync(path.join(curProjectPath, 'parasInfo.json')))
  } else {
    let paraArr = [
      "PSP",
      "RSDIN",
      "SOL_BD",
      "SOL_CBN",
      "CMN",
      "CLAY",
      "SOL_AWC",
      "RSDCO",
      "PHOSKD",
      "V_SET",
      "D50",
      "AI2",
      "RHOQ",
      "BC4",
      "RS5",
      "RS2",
      "INTER_SED_PARA_1",
      "INTER_SED_PARA_2",
      "INTER_SED_PARA_3",
      "INTER_SED_PARA_4",
      "INTER_SED_PARA_5",
      "INTER_COL_PARA_1",
      "INTER_COL_PARA_2",
      "INTER_COL_PARA_3",
      "INTER_COL_PARA_4",
      "INTER_COL_PARA_5",
      "INTER_SEDP_PARA_1",
      "INTER_SEDP_PARA_2",
      "INTER_SEDP_PARA_3",
      "INTER_SEDP_PARA_4",
      "INTER_SEDP_PARA_5",
      "INTER_COLP_PARA_1",
      "INTER_COLP_PARA_2",
      "INTER_COLP_PARA_3",
      "INTER_COLP_PARA_4",
      "INTER_COLP_PARA_5",
      "INTER_RESP_PARA_1",
      "INTER_RESP_PARA_2",
      "INTER_RESP_PARA_3",
      "INTER_RESP_PARA_4",
      "INTER_RESP_PARA_5",
      "R0",
      "R1",
      "Q_SURF_K1",
      "Q_SURF_K2",
      "Q_SOIL_K1",
      "PARA_PH0",
      "PARA_PH1",
      "PARA_PH2",
      "PARA_PH3",
      "PARA_PH4",
      "FMINN",
      "FNH3N",
      "FORGN",
      "FMINP",
      "FORGP",
    ]

    let explationArr = [
      "磷的可利用率指数",
      "表层土壤中残留物含量",
      "土壤容重",
      "表层土壤中有机碳含量",
      "腐殖质活性有机营养物的矿化速率系数",
      "黏粒含量",
      "有效水含量",
      "残留物中新生有机营养物的矿化速率系数",
      "磷的土壤分配系数",
      "水塘泥沙沉降速率",
      "河道中泥沙的中值粒径",
      "藻体磷占藻类生物质的分数",
      "20℃时当地藻类的呼吸强度",
      "20℃时当地有机磷的成矿速率常数",
      "20℃时当地有机磷的沉降速率系数",
      "20℃时沉积物提供可溶性磷的速率",
      "泥沙消纳公式中的5个系数",
      "泥沙消纳公式中的5个系数",
      "泥沙消纳公式中的5个系数",
      "泥沙消纳公式中的5个系数",
      "泥沙消纳公式中的5个系数",
      "胶体消纳公式中的5个系数",
      "胶体消纳公式中的5个系数",
      "胶体消纳公式中的5个系数",
      "胶体消纳公式中的5个系数",
      "胶体消纳公式中的5个系数",
      "大颗粒态磷消纳公式中的5个系数",
      "大颗粒态磷消纳公式中的5个系数",
      "大颗粒态磷消纳公式中的5个系数",
      "大颗粒态磷消纳公式中的5个系数",
      "大颗粒态磷消纳公式中的5个系数",
      "胶体磷消纳公式中的5个系数",
      "胶体磷消纳公式中的5个系数",
      "胶体磷消纳公式中的5个系数",
      "胶体磷消纳公式中的5个系数",
      "胶体磷消纳公式中的5个系数",
      "溶解态磷消纳公式中的5个系数",
      "溶解态磷消纳公式中的5个系数",
      "溶解态磷消纳公式中的5个系数",
      "溶解态磷消纳公式中的5个系数",
      "溶解态磷消纳公式中的5个系数",
      "壤中流下渗公式中的第一个阈值",
      "壤中流下渗公式中的第二个阈值",
      "地表径流公式中的第一个斜率",
      "地表径流公式中的第二个斜率",
      "壤中流公式中的斜率",
      "胶体流失方程四次多项式常数项",
      "胶体流失方程四次多项式一次项系数",
      "胶体流失方程四次多项式二次项系数",
      "胶体流失方程四次多项式三次项系数",
      "胶体流失方程四次多项式四次项系数",
      "化肥中无机氮的含量",
      "铵肥中无机氮的含量",
      "化肥中有机氮的含量",
      "化肥中无机磷的含量",
      "化肥中有机磷的含量",
    ]

    let danweiArr = [
      "/",
      "kg/hm2",
      "t/m3",
      "%",
      "/",
      "%",
      "/",
      "/",
      "m3/Mg",
      "m/d",
      "mm",
      "mg/mg",
      "d-1",
      "d-1",
      "d-1",
      "mg/(m2·d)",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
      "/",
    ]

    let lowerArr = [
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
      0,
      0,
      0,
      0,
      0
    ]
    let upperArr = [
      0.7,
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
      0.5,
      0.5,
      0.5,
      0.5,
      0.5,
    ]

    let defaultArr = [
      0.4,
      1000,
      1.8,
      1,
      0.001,
      20,
      0.1,
      0.055,
      175,
      5,
      50,
      0.015,
      0.1,
      0.1,
      0.001,
      0.001,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      1.5,
      50,
      200,
      100,
      100,
      100,
      -13000,
      8000,
      -4000,
      200,
      -10,
      0.2,
      0.2,
      0.2,
      0.2,
      0.2
    ]

    let parasObj = []
    for (let i = 0; i < defaultArr.length; i++) {
      parasObj.push({
        para: paraArr[i],
        explaination: explationArr[i],
        unit: danweiArr[i],
        lower: lowerArr[i],
        upper: upperArr[i],
        default: defaultArr[i],
        value: defaultArr[i]
      })
    }
    fs.writeFileSync(path.join(curProjectPath, 'parasInfo.json'), JSON.stringify(parasObj))
    return parasObj
  }

}