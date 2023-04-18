export interface ProjectInfo {
  projectName: string,
  projectPath: string,
  lastSaved: string,
  lastSavedStamp: number,
  area: string,
  periods: {
    startDate: string,
    endDate: string
  },
  rainfall: {
    state: boolean
  },
  landUse: {
    state: boolean,
    grids: number,
  },
  soilType: {
    state: boolean,
    grids: number,
  },
  DEM: {
    state: boolean,
    grids: number,
  },
  D8: {
    state: boolean,
    grids: number,
  },
  rusle: {
    S_factor: boolean,
    C_factor: boolean,
    L_factor: boolean,
  },
  observeData: {
    TP: {
      checked: boolean,
      imported: boolean
    },
    sedP: {
      checked: boolean,
      imported: boolean
    },
    solP: {
      checked: boolean,
      imported: boolean
    },
    sed: {
      checked: boolean,
      imported: boolean
    },
    colP: {
      checked: boolean,
      imported: boolean
    },
    col: {
      checked: boolean,
      imported: boolean
    }
  }
}