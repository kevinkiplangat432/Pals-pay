import { configureStore } from '@reduxjs/toolkit';
import adminUsersReducer from './slices/adminUsersSlice';
import adminWalletsReducer from './slices/adminWalletsSlice';
import adminTransactionsReducer from './slices/adminTransactionsSlice';
import adminAnalyticsReducer from './slices/adminAnalyticsSlice';
import adminKycReducer from './slices/adminKycSlice';
import authSlice from '../features/authSlice';
import userReducer from '../features/profileSlice';
import walletReducer from '../features/walletSlice';
import transactionsReducer from '../features/transactionsSlice';
import paymentMethodsReducer from '../features/paymentMethodsSlice';

export const store = configureStore({
  reducer: {
    adminUsers: adminUsersReducer,
    adminWallets: adminWalletsReducer,
    adminTransactions: adminTransactionsReducer,
    adminAnalytics: adminAnalyticsReducer,
    adminKyc: adminKycReducer,
    auth: authSlice,
    user: userReducer,
    wallet: walletReducer,
    transactions: transactionsReducer,
    paymentMethods: paymentMethodsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['adminAnalytics/fetchSystemStats/fulfilled'],
        ignoredPaths: ['adminAnalytics.lastUpdated'],
      },
    }),
});
