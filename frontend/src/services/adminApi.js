import api from "./api";

// Users API
export const fetchAllUsers = async (params = {}) => {
  const response = await api.get("/admin/users", { params });
  return response.data;
};

export const toggleUserStatus = async (userId, isActive) => {
  const response = await api.put(`/admin/users/${userId}/status`, {
    is_active: isActive,
  });
  return response.data;
};

// Wallets API
export const fetchAllWallets = async (params = {}) => {
  const response = await api.get("/admin/wallets", { params });
  return response.data;
};

// Transactions API
export const fetchAllTransactions = async (params = {}) => {
  const response = await api.get("/admin/transactions", { params });
  return response.data;
};

export const reverseTransaction = async (txId, otpCode) => {
  const response = await api.post(
    `/admin/transactions/${txId}/reverse`,
    {},
    { headers: { "X-OTP-Code": otpCode } }
  );
  return response.data;
};

// Analytics API
export const fetchSystemStats = async () => {
  const response = await api.get("/admin/stats");
  return response.data;
};

export const fetchProfitTrends = async (days = 30) => {
  const response = await api.get("/admin/analytics/profit-trends", {
    params: { days },
  });
  return response.data;
};

export const fetchSuspiciousActivities = async () => {
  const response = await api.get("/admin/suspicious-activities");
  return response.data;
};

// KYC API
export const fetchPendingKyc = async (params = {}) => {
  const response = await api.get("/admin/kyc/pending", { params });
  return response.data;
};

export const verifyKyc = async (kycId, approved, rejectionReason = null) => {
  const response = await api.post(`/admin/kyc/${kycId}/verify`, {
    approved,
    rejection_reason: rejectionReason,
  });
  return response.data;
};

// Audit Logs API
export const fetchAuditLogs = async (params = {}) => {
  const response = await api.get("/admin/audit-logs", { params });
  return response.data;
};