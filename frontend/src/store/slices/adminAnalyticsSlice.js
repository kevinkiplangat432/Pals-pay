import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  fetchSystemStats,
  fetchProfitTrends,
  fetchSuspiciousActivities,
} from '../../services/adminApi';

export const loadSystemStats = createAsyncThunk(
  'adminAnalytics/loadSystemStats',
  async (_, { rejectWithValue }) => {
    try {
      const data = await fetchSystemStats();
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const loadProfitTrends = createAsyncThunk(
  'adminAnalytics/loadProfitTrends',
  async (days = 30, { rejectWithValue }) => {
    try {
      const data = await fetchProfitTrends(days);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const loadSuspiciousActivities = createAsyncThunk(
  'adminAnalytics/loadSuspiciousActivities',
  async (_, { rejectWithValue }) => {
    try {
      const data = await fetchSuspiciousActivities();
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

const adminAnalyticsSlice = createSlice({
  name: 'adminAnalytics',
  initialState: {
    systemStats: null,
    profitTrends: null,
    suspiciousActivities: null,
    loading: false,
    error: null,
    trendsDays: 30,
  },
  reducers: {
    setTrendsDays: (state, action) => {
      state.trendsDays = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadSystemStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadSystemStats.fulfilled, (state, action) => {
        state.loading = false;
        state.systemStats = action.payload;
      })
      .addCase(loadSystemStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to load system stats';
      })
      .addCase(loadProfitTrends.fulfilled, (state, action) => {
        state.profitTrends = action.payload;
      })
      .addCase(loadProfitTrends.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to load profit trends';
      })
      .addCase(loadSuspiciousActivities.fulfilled, (state, action) => {
        state.suspiciousActivities = action.payload;
      })
      .addCase(loadSuspiciousActivities.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to load suspicious activities';
      });
  },
});

export const { setTrendsDays, clearError } = adminAnalyticsSlice.actions;
export default adminAnalyticsSlice.reducer;
