import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchPendingKyc, verifyKyc } from '../../services/adminApi';

export const loadPendingKyc = createAsyncThunk(
  'adminKyc/loadPendingKyc',
  async (params, { rejectWithValue }) => {
    try {
      const data = await fetchPendingKyc(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const verifyKycAction = createAsyncThunk(
  'adminKyc/verifyKyc',
  async ({ kycId, approved, rejectionReason }, { rejectWithValue }) => {
    try {
      const data = await verifyKyc(kycId, approved, rejectionReason);
      return { kycId, ...data };
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

const adminKycSlice = createSlice({
  name: 'adminKyc',
  initialState: {
    kycVerifications: [],
    total: 0,
    pages: 0,
    currentPage: 1,
    loading: false,
    error: null,
    filters: {
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
      .addCase(loadPendingKyc.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadPendingKyc.fulfilled, (state, action) => {
        state.loading = false;
        state.kycVerifications = action.payload.kyc_verifications;
        state.total = action.payload.total;
        state.pages = action.payload.pages;
        state.currentPage = action.payload.current_page;
      })
      .addCase(loadPendingKyc.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to load KYC verifications';
      })
      .addCase(verifyKycAction.fulfilled, (state, action) => {
        state.kycVerifications = state.kycVerifications.filter(
          (kyc) => kyc.id !== action.payload.kycId
        );
        state.total = Math.max(0, state.total - 1);
      })
      .addCase(verifyKycAction.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to verify KYC';
      });
  },
});

export const { setFilters, clearError } = adminKycSlice.actions;
export default adminKycSlice.reducer;
