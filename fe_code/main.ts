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
        soilType: {
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
    curProjectInfo = data[0]
    curProjectPath = curProjectInfo.projectPath
    return data
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
          if (rainfallInfo == 'err' || rainfallInfo.toString() == 'err') {
            reject({
              status: 400,
              msg: 'rainfallErr'
            })
          }
          updateStatus([
            { target: ['rainfall', 'value'], value: rainfallInfo.toString().replace(/'/g, '"') },
            { target: ['rainfall', 'state'], value: true }
          ])
          resolve({
            status: 200,
            msg: curProjectInfo
          })
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