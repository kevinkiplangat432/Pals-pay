import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { apiFetch } from "../app/api";

export const fetchPaymentMethods = createAsyncThunk("payment/methods/list", async () => {
    return await apiFetch("/user/payment-methods");
});

export const addPaymentMethod = createAsyncThunk("payment/methods/add", async (methodData) => {
    return await apiFetch("/user/payment-methods", {
        method: "POST",
        body: methodData,
    });
});

export const deletePaymentMethod = createAsyncThunk("payment/methods/delete", async (methodId) => {
    return await apiFetch(`/user/payment-methods/${methodId}`, {
        method: "DELETE",
    });
});

export const setDefaultPaymentMethod = createAsyncThunk("payment/methods/set-default", async (methodId) => {
    return await apiFetch(`/user/payment-methods/${methodId}/default`, {
        method: "PUT",
    });
});

export const verifyPaymentMethod = createAsyncThunk("payment/methods/verify", async ({id, verification_token}) => {
    return await apiFetch(`/user/payment-methods/${id}/verify`, {
        method: "POST",
        body:{verification_token},
    });
});

const slice = createSlice({
    name: "paymentMethods",
    initialState: {
        items : [],
        status: "idle",
        error: null,
        success: null,
    },
    reducers: {
        clearPaymentMethodMessages(state) {
            state.error = null;
            state.success = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch Payment Methods
            .addCase(fetchPaymentMethods.pending, (state) => {
                state.status = "loading"; state.error = null;
            })
            .addCase(fetchPaymentMethods.fulfilled, (state, action) => {
                state.status = "succeeded";
                state.items = action.payload.payment_methods??[];
             })
            .addCase(fetchPaymentMethods.rejected, (state, action) => {
                state.status = "failed";
                state.error = action.error.message;
            })
            
            .addCase(addPaymentMethod.fulfilled, (state, action) => {
                state.success = action.payload.message || "Payment method added successfully.";
            })
            .addCase(deletePaymentMethod.fulfilled, (state, action) => {
                state.success = action.payload.message || "Payment method deleted successfully.";
            })
            .addCase(setDefaultPaymentMethod.fulfilled, (state, action) => {
                state.success = action.payload.message || "Default payment method set successfully.";
            })
            .addCase(verifyPaymentMethod.fulfilled, (state, action) => {
                state.success = action.payload.message || "Payment method verified successfully.";
            });
    },
});

export const { clearPaymentMethodMessages } = slice.actions;

export default slice.reducer;