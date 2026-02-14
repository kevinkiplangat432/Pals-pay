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

export const transferToBeneficiaryWallet = createAsyncThunk("wallet/transferToBeneficiaryWallet", async ({ beneficiary_wallet_id, amount, description }) => {
    return await apiFetch("/transfer", {
        method: "POST",
        body: { beneficiary_wallet_id, amount, description },
    });
});

export const transferToPhone = createAsyncThunk("wallet/transferToPhone", async ({ phone_number, amount, description }) => {
    return await apiFetch("/transfer", {
        method: "POST",
        body: { phone_number, amount, description },
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
            .addCase(transferToBeneficiaryWallet.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(transferToBeneficiaryWallet.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.success = "Transfer to beneficiary wallet successful.";
            })
            .addCase(transferToBeneficiaryWallet.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            .addCase(transferToPhone.pending, (state) => {
                state.status = "loading";
                state.error = null;
            })
            .addCase(transferToPhone.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.success = action.payload?.message || "Transfer to phone successful.";
            })
            .addCase(transferToPhone.rejected, (state, action) => {
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