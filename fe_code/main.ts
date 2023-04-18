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
      let prjectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
      prjectInfos.push(projectInfo)
      fs.writeFileSync(projectInfoJson, JSON.stringify(prjectInfos))
    }
    return ProjectPath
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    webPreferences: {
      preload: path.join(__dirname, 'render.ts')
    }
  })
  ipcMain.handle('createNewProject', createNewProject)
  mainWindow.loadURL("http://localhost:3000/");

  // 检查项目JSON文件是否存在，若存在则返回所有项目的信息。
  if (!fs.existsSync(projectInfoJson)) {
    fs.writeFileSync(projectInfoJson, JSON.stringify([]))
  } else {
    ipcMain.handle('requireProjectInfo', () => {
      let data = fs.readFileSync(projectInfoJson)
      return JSON.parse(data)
    })
  }

  ipcMain.handle('deleteProject', (e, payload) => {
    let projectInfos = JSON.parse(fs.readFileSync(projectInfoJson))
    let newProjectInfos = projectInfos.filter((info) => info.projectName !== payload)
    fs.writeFileSync(projectInfoJson, JSON.stringify(newProjectInfos))
    console.log(`项目${payload}删除成功`);
    return {
      status: 200,
      msg: 'ok'
    }
  })
}
function checkJson() { }


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