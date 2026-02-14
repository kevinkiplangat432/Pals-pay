import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { apiFetch } from "../app/api";


export const register = createAsyncThunk(
  "auth/register",
  async (userData, { rejectWithValue }) => {
    try {
      const data = await apiFetch("/auth/register", {
        method: "POST",
        body: userData,
      });

      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const login = createAsyncThunk(
  "auth/login",
  async (credentials, { rejectWithValue }) => {
    try {
      const data = await apiFetch("/auth/login", {
        method: "POST",
        body: credentials,
      });

      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const verifyLoginOTP = createAsyncThunk(
  "auth/verifyLoginOTP",
  async ({ user_id, otp_code }, { rejectWithValue }) => {
    try {
      const data = await apiFetch("/auth/login/verify-otp", {
        method: "POST",
        body: { user_id, otp_code },
      });

      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const logout = createAsyncThunk("auth/logout", async () => {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    return true;
  }
});

export const fetchUserProfile = createAsyncThunk(
  "auth/fetchUserProfile",
  async (_, { rejectWithValue }) => {
    try {
      const data = await apiFetch("/user/profile");
      localStorage.setItem("user", JSON.stringify(data));
      return data;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);


const authSlice = createSlice({
  name: "auth",
  initialState: {
    user: JSON.parse(localStorage.getItem("user")) || null,
    status: "idle",
    error: null,
    otpRequired: false,
    otpUserId: null,
  },
  reducers: {
    clearAuthError: (state) => {
      state.error = null;
    },
    setUser: (state, action) => {
      state.user = action.payload;
      localStorage.setItem("user", JSON.stringify(action.payload));
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = "succeeded";
        if (action.payload.requires_otp) {
          state.otpRequired = true;
          state.otpUserId = action.payload.user_id;
        } else {
          state.user = action.payload.user;
          state.otpRequired = false;
          state.otpUserId = null;
        }
      })
      .addCase(login.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // Register
      .addCase(register.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
      })
      .addCase(register.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // Verify OTP
      .addCase(verifyLoginOTP.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(verifyLoginOTP.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.otpRequired = false;
        state.otpUserId = null;
      })
      .addCase(verifyLoginOTP.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Invalid OTP code. Please try again.";
      })

      // Fetch Profile
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.user = action.payload;
      })

      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.otpRequired = false;
        state.otpUserId = null;
      });
  },
});

export const { clearAuthError, setUser } = authSlice.actions;
export default authSlice.reducer;
