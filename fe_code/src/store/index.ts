import { configureStore } from '@reduxjs/toolkit'
import reduxLogger from 'redux-logger'
import reduxThunk from 'redux-thunk'
import dataManagementReducer from './features/dataManagementSlice'


const store = configureStore({
  reducer: { dataManagementReducer },
  middleware: [reduxThunk]
})
export default store