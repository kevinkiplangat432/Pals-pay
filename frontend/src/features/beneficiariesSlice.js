import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { apiFetch } from "../app/api";

export const fetchBeneficiaries = createAsyncThunk(
  "beneficiaries/fetch",
  async (_, { rejectWithValue }) => {
    try {
      return await apiFetch("/beneficiaries");
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const addBeneficiary = createAsyncThunk(
  "beneficiaries/add",
  async (beneficiaryData, { rejectWithValue }) => {
    try {
      return await apiFetch("/beneficiaries", {
        method: "POST",
        body: beneficiaryData,
      });
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const deleteBeneficiary = createAsyncThunk(
  "beneficiaries/delete",
  async (id, { rejectWithValue }) => {
    try {
      return await apiFetch(`/beneficiaries/${id}`, {
        method: "DELETE",
      });
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateBeneficiary = createAsyncThunk(
  "beneficiaries/update",
  async ({ id, data }, { rejectWithValue }) => {
    try {
      return await apiFetch(`/beneficiaries/${id}`, {
        method: "PUT",
        body: data,
      });
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const beneficiariesSlice = createSlice({
  name: "beneficiaries",
  initialState: {
    items: [],
    status: "idle",
    error: null,
  },
  reducers: {
    clearBeneficiariesError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBeneficiaries.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchBeneficiaries.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload.beneficiaries || [];
      })
      .addCase(fetchBeneficiaries.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })
      .addCase(addBeneficiary.fulfilled, (state, action) => {
        state.items.push(action.payload.beneficiary);
      })
      .addCase(deleteBeneficiary.fulfilled, (state, action) => {
        state.items = state.items.filter(
          (item) => item.id !== action.meta.arg
        );
      });
  },
});

export const { clearBeneficiariesError } = beneficiariesSlice.actions;
export default beneficiariesSlice.reducer;