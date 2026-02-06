import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchAllWallets } from '../../services/adminApi';

export const loadWallets = createAsyncThunk(
  'adminWallets/loadWallets',
  async (params, { rejectWithValue }) => {
    try {
      const data = await fetchAllWallets(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

const adminWalletsSlice = createSlice({
  name: 'adminWallets',
  initialState: {
    wallets: [],
    total: 0,
    pages: 0,
    currentPage: 1,
    loading: false,
    error: null,
    filters: {
      status: '',
      search: '',
      min_balance: '',
      page: 1,
      per_page: 20,
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
      .addCase(loadWallets.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadWallets.fulfilled, (state, action) => {
        state.loading = false;
        state.wallets = action.payload.wallets;
        state.total = action.payload.total;
        state.pages = action.payload.pages;
        state.currentPage = action.payload.current_page;
      })
      .addCase(loadWallets.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to load wallets';
      });
  },
});

export const { setFilters, clearError } = adminWalletsSlice.actions;
export default adminWalletsSlice.reducer;
