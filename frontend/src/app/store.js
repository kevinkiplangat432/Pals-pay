//Redux Store
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './features/authSlice';
import profileReducer from './features/profileSlice';
import paymentMethodsReducer from './features/paymentMethodsSlice';
import walletReducer from './features/walletSlice';
import beneficiariesReducer from './features/beneficiariesSlice';
import transactionsReducer from './features/transactionsSlice';


export const store = configureStore({
  reducer: {
    auth: authReducer,
    profile: profileReducer,
    paymentMethods: paymentMethodsReducer,
    wallet: walletReducer,
    beneficiaries: beneficiariesReducer,
    transactions: transactionsReducer,
  },
});
