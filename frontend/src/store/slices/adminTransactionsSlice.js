import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchAllTransactions, reverseTransaction } from '../../services/adminApi';

export const loadTransactions = createAsyncThunk(
  'adminTransactions/loadTransactions',
  async (params, { rejectWithValue }) => {
    try {
      const data = await fetchAllTransactions(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const reverseTransactionAction = createAsyncThunk(
  'adminTransactions/reverseTransaction',
  async ({ txId, otpCode }, { rejectWithValue }) => {
    try {
      const data = await reverseTransaction(txId, otpCode);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

const adminTransactionsSlice = createSlice({
  name: 'adminTransactions',
  initialState: {
    transactions: [],
    total: 0,
    pages: 0,
    currentPage: 1,
    loading: false,
    error: null,
    filters: {
      status: '',
      type: '',
      start_date: '',
      end_date: '',
      min_amount: '',
      max_amount: '',
      page: 1,
      per_page: 50,
    },
  },
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadTransactions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadTransactions.fulfilled, (state, action) => {
        state.loading = false;
        state.transactions = action.payload.transactions;
        state.total = action.payload.total;
        state.pages = action.payload.pages;
        state.currentPage = action.payload.current_page;
      })
      .addCase(loadTransactions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to load transactions';
      })
      .addCase(reverseTransactionAction.fulfilled, (state, action) => {
        const reversedTx = action.payload.original_transaction;
        const index = state.transactions.findIndex((tx) => tx.id === reversedTx.id);
        if (index !== -1) {
          state.transactions[index] = reversedTx;
        }
      })
      .addCase(reverseTransactionAction.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to reverse transaction';
      });
  },
});

export const { setFilters, clearError } = adminTransactionsSlice.actions;
export default adminTransactionsSlice.reducer;
