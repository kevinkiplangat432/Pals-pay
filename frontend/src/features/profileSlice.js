import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { apiFetch } from "../app/api";

// Profile
export const fetchUserProfile = createAsyncThunk("user/profile/get", async () => {
    return await apiFetch("/api/user/profile");
});

export const updateUserProfile = createAsyncThunk("user/profile/update", async (profileData) => {
    return await apiFetch("/api/user/profile", {
        method: "PUT",
        body: profileData,
    });
});

export const changePassword = createAsyncThunk("user/password/change", async (passwordData) => {
    return await apiFetch("/api/user/password", {
        method: "PUT",
        body: passwordData,
    });
});

export const fetchKycStatus = createAsyncThunk("user/kyc/status", async () => {
    return await apiFetch("/api/user/kyc-status");
});

export const submitKycDocuments = createAsyncThunk("user/kyc/submit", async (kycData) => {
    const fd = new FormData();
    fd.append("document_type", kycData.document_type);
    fd.append("document_number", kycData.document_number);
    fd.append("front_document", kycData.front_document);
    if (kycData.back_document) fd.append("back_document", kycData.back_document);
    if (kycData.selfie) fd.append("selfie", kycData.selfie);

    return await apiFetch("/api/user/kyc/submit", {method: "POST", body: fd});
});

const userSlice = createSlice({
    name: "user",
    initialState: {
        profile: null,
        kyc: null,
        status: "idle",
        error: null,
        success: null,
    },
    reducers: {
        clearUserMessages(state) {
            state.error = null;
            state.success = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Fetch Profile
            .addCase(fetchUserProfile.pending, (state) => {
                state.status = "loading"; state.error = null;
            })
            .addCase(fetchUserProfile.fulfilled, (state, action) => {
                state.status = "succeeded"; state.profile = action.payload;
            })
            .addCase(fetchUserProfile.rejected, (state, action) => {
                state.status = "failed"; state.error = action.error.message;
            })
            // Update Profile
            .addCase(updateUserProfile.pending, (state) => {
                state.status = "loading"; state.error = null; state.success = null;
            })
            .addCase(updateUserProfile.fulfilled, (state, action) => {
                state.status = "succeeded"; 
                state.profile = action.payload.user ?? action.payload;
                state.success = action.payload.message || "Profile updated successfully.";
            })
            .addCase(updateUserProfile.rejected, (state, action) => {
                state.status = "failed"; state.error = action.error.message;
            })

            // password
            .addCase(changePassword.pending, (state) => {
                state.status = "loading"; state.error = null; state.success = null;
            })
            .addCase(changePassword.fulfilled, (state, action) => {
                state.status = "succeeded"; 
                state.success = action.payload.message || "Password changed successfully.";
            })
            .addCase(changePassword.rejected, (state, action) => {
                state.status = "failed"; state.error = action.error.message;
            })

            // kyc
            .addCase(fetchKycStatus.pending, (state) => {
                state.status = "loading"; state.error = null;
            })
            .addCase(fetchKycStatus.fulfilled, (state, action) => {
                state.status = "succeeded"; state.kyc = action.payload;
            })
            .addCase(fetchKycStatus.rejected, (state, action) => {
                state.status = "failed"; state.error = action.error.message;
            })
            
            .addCase(submitKycDocuments.pending, (state) => {
                state.status = "loading"; state.error = null; state.success = null;
            })
            .addCase(submitKycDocuments.fulfilled, (state, action) => {
                state.status = "succeeded"; 
                state.success = action.payload.message || "KYC documents submitted successfully.";
            })
            .addCase(submitKycDocuments.rejected, (state, action) => {
                state.status = "failed"; state.error = action.error.message;
            });
    }
});
export const { clearUserMessages } = userSlice.actions;

export default userSlice.reducer;