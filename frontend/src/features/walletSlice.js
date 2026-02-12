import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { apiFetch } from '../app/api';

export const fetchWalletSummary = createAsyncThunk("wallet/summary", async () => {
    return await apiFetch("/wallet/summary");
});

export const fetchWalletAnalytics = createAsyncThunk("wallet/analytics", async () => {
    return await apiFetch("/wallet/analytics");
});

export const depositMpesa = createAsyncThunk("wallet/depositMpesa", async ({ amount, phone_number }, { rejectWithValue }) => {
    try {
        console.log('Initiating M-Pesa deposit:', { amount, phone_number });
        const response = await apiFetch("/deposit/mpesa", {
            method: "POST",
            body: { amount, phone_number },
        });
        console.log('M-Pesa deposit response:', response);
        return response;
    } catch (error) {
        console.error('M-Pesa deposit error:', error);
        return rejectWithValue(error.message);
    }
});

export const transferFunds = createAsyncThunk("wallet/transferFunds", async ({ receiver_phone, amount, description }) => {
    return await apiFetch("/transfer", {
        method: "POST",
        body: { receiver_phone, amount, description },
    });
});

export const withdrawFunds = createAsyncThunk("wallet/withdrawFunds", async ({ amount, payment_method_id }) => {
    return await apiFetch("/withdraw", {
        method: "POST",
        body: { amount, payment_method_id },
    });
});

export const fetchTransactionSummary = createAsyncThunk(
    "wallet/transactionSummary", 
    async ({ days = 30} = {}) => {
        const qs = new URLSearchParams();
        qs.set("days", String(days));
        return await apiFetch(`/wallet/transactions/summary?${qs.toString()}`);
    }
);

const walletSlice = createSlice({
    name: "wallet",
    initialState: {
        summary: null,
        analytics: null,
        transactionSummary: null,
        status: "idle",
        error: null,
        success: null,
    },
    reducers: {
        clearWalletMessages(state) {
            state.error = null;
            state.success = null;
    },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchWalletSummary.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(fetchWalletSummary.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.summary = action.payload;
            })
            .addCase(fetchWalletSummary.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            .addCase(fetchWalletAnalytics.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(fetchWalletAnalytics.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.analytics = action.payload;
            })
            .addCase(fetchWalletAnalytics.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            .addCase(fetchTransactionSummary.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(fetchTransactionSummary.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.transactionSummary = action.payload;
            })
            .addCase(fetchTransactionSummary.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            .addCase(depositMpesa.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(depositMpesa.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.success = "Mpesa deposit initiated successfully.";
            })
            .addCase(depositMpesa.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.payload || action.error.message || "Deposit failed";
            })
            .addCase(transferFunds.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(transferFunds.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.success = action.payload?.message || "Transfer successful.";
            })
            .addCase(transferFunds.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            .addCase(withdrawFunds.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(withdrawFunds.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.success = "Withdrawal successful.";
            })
            .addCase(withdrawFunds.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            });
    }
});

export const { clearWalletMessages } = walletSlice.actions;

export default walletSlice.reducer;