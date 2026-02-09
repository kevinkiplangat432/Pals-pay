import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchAllUsers, toggleUserStatus } from '../../services/adminApi';

export const loadUsers = createAsyncThunk(
  'adminUsers/loadUsers',
  async (params, { rejectWithValue }) => {
    try {
      const data = await fetchAllUsers(params);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

export const updateUserStatus = createAsyncThunk(
  'adminUsers/updateUserStatus',
  async ({ userId, isActive }, { rejectWithValue }) => {
    try {
      const data = await toggleUserStatus(userId, isActive);
      return data;
    } catch (error) {
      return rejectWithValue(error.response?.data || { message: error.message });
    }
  }
);

const adminUsersSlice = createSlice({
  name: 'adminUsers',
  initialState: {
    users: [],
    total: 0,
    pages: 0,
    currentPage: 1,
    loading: false,
    error: null,
    filters: {
      status: '',
      kyc_status: '',
      search: '',
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
      .addCase(loadUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload.users;
        state.total = action.payload.total;
        state.pages = action.payload.pages;
        state.currentPage = action.payload.current_page;
      })
      .addCase(loadUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to load users';
      })
      .addCase(updateUserStatus.fulfilled, (state, action) => {
        const updatedUser = action.payload.user;
        const index = state.users.findIndex((user) => user.id === updatedUser.id);
        if (index !== -1) {
          state.users[index] = updatedUser;
        }
      })
      .addCase(updateUserStatus.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to update user status';
      });
  },
});

export const { setFilters, clearError } = adminUsersSlice.actions;
export default adminUsersSlice.reducer;
