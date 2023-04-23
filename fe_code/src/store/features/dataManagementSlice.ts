// 数据管理的切片
import { createSlice } from '@reduxjs/toolkit'
import { ProjectInfo } from "../../interface/index.ts";

type updateType = { target: string[], value: any }[]


const dataManagementSlice = createSlice({
  // 切片的名称
  name: 'dataManagement',
  // 初始状态
  initialState: {
    allProjectInfos: [],
    curProjectInfo: {}
  },
  // 编写业务逻辑的reducer
  reducers: {
    updateStatus(state: any, { payload }) {
      state.curProjectInfo = payload
    },
    getStatus(state: any, { payload }) {
      if (!payload) {
        state.allProjectInfos = []
        state.curProjectInfo = {}
        return
      }
      state.allProjectInfos = payload
      state.curProjectInfo = state.allProjectInfos.sort((a, b) => b.lastSavedStamp - a.lastSavedStamp)[0]
    },
    switchProject(state: any, { payload }) {
      state.curProjectInfo = state.allProjectInfos.filter(
        (info) => info.projectName == payload.name
      )[0]
    },
  }
})

export const { updateStatus, getStatus, switchProject } = dataManagementSlice.actions
// 异步派发
export const getProjectInfoAsync = () => {
  return async (dispatch: Function) => {
    let projectInfos = await window.electronAPI.requireProjectInfo();

    dispatch(getStatus(projectInfos))
  }
}

export const updateStatusAsync = (payload: updateType) => {
  return async (dispatch: Function, getState: Function): Promise<void> => {
    let state = getState()
    let newPayload = { projectName: state.dataManagementReducer.curProjectInfo.projectName, payload }
    let updatedInfo = await window.electronAPI.updateProjectInfo(newPayload);
    console.log(updatedInfo);
    dispatch(updateStatus(updatedInfo))
  }
}

export default dataManagementSlice.reducer