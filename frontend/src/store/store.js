import { configureStore } from '@reduxjs/toolkit';
import adminUsersReducer from './slices/adminUsersSlice';
import adminWalletsReducer from './slices/adminWalletsSlice';
import adminTransactionsReducer from './slices/adminTransactionsSlice';
import adminAnalyticsReducer from './slices/adminAnalyticsSlice';
import adminKycReducer from './slices/adminKycSlice';
import authSlice from '../features/authSlice';

export const store = configureStore({
  reducer: {
    adminUsers: adminUsersReducer,
    adminWallets: adminWalletsReducer,
    adminTransactions: adminTransactionsReducer,
    adminAnalytics: adminAnalyticsReducer,
    adminKyc: adminKycReducer,
    auth: authSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['adminAnalytics/fetchSystemStats/fulfilled'],
        ignoredPaths: ['adminAnalytics.lastUpdated'],
      },
    }),
});
