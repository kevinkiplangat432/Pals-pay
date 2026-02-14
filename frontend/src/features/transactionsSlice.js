import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { apiFetch } from "../app/api";

export const fetchTransactions = createAsyncThunk(
    "transactions/list",
    async ({ page = 1, per_page = 20, type} = {}) => {
        const qs = new URLSearchParams();
        qs.set("page", String(page));
        qs.set("per_page", String(per_page));
        if (type) qs.set("type", type);
        return await apiFetch(`/user/transactions?${qs.toString()}`);
    }
);

const slice = createSlice({
    name: "transactions",
    initialState: { data: null, status: "idle", error: null },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchTransactions.pending, (state) => {
                state.status = "loading"; state.error = null;
            })
            .addCase(fetchTransactions.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.data = action.payload;
             })
            .addCase(fetchTransactions.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            });
    },
});

export default slice.reducer;