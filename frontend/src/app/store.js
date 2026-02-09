import { configureStore } from "@reduxjs/toolkit";
import authReducer from "../features/authSlice";
import profileReducer from "../features/profileSlice";
import paymentMethodsReducer from "../features/paymentMethodsSlice";
import walletReducer from "../features/walletSlice";
import beneficiariesReducer from "../features/beneficiariesSlice";
import transactionsReducer from "../features/transactionsSlice";

// Import admin slices
import adminUsersReducer from "../store/slices/adminUsersSlice";
import adminWalletsReducer from "../store/slices/adminWalletsSlice";
import adminTransactionsReducer from "../store/slices/adminTransactionsSlice";
import adminAnalyticsReducer from "../store/slices/adminAnalyticsSlice";
import adminKycReducer from "../store/slices/adminKycSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    profile: profileReducer,
    paymentMethods: paymentMethodsReducer,
    wallet: walletReducer,
    beneficiaries: beneficiariesReducer,
    transactions: transactionsReducer,
    // Admin reducers
    adminUsers: adminUsersReducer,
    adminWallets: adminWalletsReducer,
    adminTransactions: adminTransactionsReducer,
    adminAnalytics: adminAnalyticsSlice,
    adminKyc: adminKycReducer,
  },
});