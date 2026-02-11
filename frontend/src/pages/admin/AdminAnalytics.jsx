import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import StatsCard from "../../components/admin/StatsCard";
import LoadingSpinner from "../../components/common/LoadingSpinner";
import ErrorMessage from "../../components/common/ErrorMessage";
import {
  loadSystemStats,
  loadProfitTrends,
  loadSuspiciousActivities,
  setTrendsDays,
} from "../../store/slices/adminAnalyticsSlice";

const AdminAnalytics = () => {
  const dispatch = useDispatch();
  const {
    systemStats,
    profitTrends,
    suspiciousActivities,
    loading,
    error,
    trendsDays,
  } = useSelector((state) => state.adminAnalytics);

  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    dispatch(loadSystemStats());
    dispatch(loadProfitTrends(trendsDays));
    dispatch(loadSuspiciousActivities());
  }, [dispatch, trendsDays]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-KE", {
      style: "currency",
      currency: "KES",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat("en-KE").format(num);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 rounded-lg ${
              activeTab === "overview"
                ? "bg-green-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("profit")}
            className={`px-4 py-2 rounded-lg ${
              activeTab === "profit"
                ? "bg-green-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Profit Trends
          </button>
          <button
            onClick={() => setActiveTab("suspicious")}
            className={`px-4 py-2 rounded-lg ${
              activeTab === "suspicious"
                ? "bg-green-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Suspicious Activity
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Overview Tab */}
          {activeTab === "overview" && systemStats && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatsCard
                  title="Total Users"
                  value={formatNumber(systemStats.users?.total || 0)}
                  icon="users"
                  color="bg-blue-100"
                  subtitle={`${systemStats.users?.active || 0} active`}
                />
                <StatsCard
                  title="Today's Volume"
                  value={formatCurrency(systemStats.transactions?.today_volume || 0)}
                  icon="dollar"
                  color="bg-green-100"
                  subtitle={`${systemStats.transactions?.today_count || 0} transactions`}
                />
                <StatsCard
                  title="Total Balance"
                  value={formatCurrency(systemStats.wallets?.total_balance || 0)}
                  icon="wallet"
                  color="bg-yellow-100"
                  subtitle={`${systemStats.wallets?.total || 0} wallets`}
                />
                <StatsCard
                  title="Monthly Fees"
                  value={formatCurrency(systemStats.transactions?.fees_last_30_days || 0)}
                  icon="chart"
                  color="bg-purple-100"
                  subtitle="Last 30 days"
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    User Statistics
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">KYC Verified</span>
                      <span className="font-medium">
                        {systemStats.users?.kyc_verified || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">KYC Pending</span>
                      <span className="font-medium">
                        {systemStats.users?.kyc_pending || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">New Today</span>
                      <span className="font-medium">
                        {systemStats.users?.new_today || 0}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Transaction Statistics
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last 30 Days</span>
                      <span className="font-medium">
                        {formatNumber(systemStats.transactions?.total_last_30_days || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completed</span>
                      <span className="font-medium">
                        {formatNumber(systemStats.transactions?.completed_last_30_days || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Volume</span>
                      <span className="font-medium">
                        {formatCurrency(systemStats.transactions?.volume_last_30_days || 0)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Profit Trends Tab */}
          {activeTab === "profit" && profitTrends && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Profit Trends - Last {trendsDays} Days
                </h3>
                <select
                  value={trendsDays}
                  onChange={(e) => dispatch(setTrendsDays(Number(e.target.value)))}
                  className="border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value={7}>Last 7 Days</option>
                  <option value={30}>Last 30 Days</option>
                  <option value={90}>Last 90 Days</option>
                </select>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h4 className="text-md font-medium text-gray-900 mb-4">
                  Daily Profit Trends
                </h4>
                <div className="space-y-3">
                  {profitTrends.daily_trends?.map((trend, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{trend.date}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-medium">
                          {formatCurrency(trend.total_fees)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {trend.transaction_count} transactions
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {profitTrends.top_users && profitTrends.top_users.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h4 className="text-md font-medium text-gray-900 mb-4">
                    Top Users by Fees Generated
                  </h4>
                  <div className="space-y-3">
                    {profitTrends.top_users.map((user, index) => (
                      <div key={user.user_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-gray-500">#{index + 1}</span>
                          <div>
                            <div className="font-medium">{user.username}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">
                            {formatCurrency(user.total_fees)}
                          </div>
                          <div className="text-sm text-gray-500">
                            {user.transaction_count} transactions
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Suspicious Activity Tab */}
          {activeTab === "suspicious" && suspiciousActivities && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Suspicious Activity Monitoring
              </h3>

              {suspiciousActivities.large_transactions &&
                suspiciousActivities.large_transactions.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-md font-medium text-gray-900 mb-4">
                      Large Transactions (Last 24 Hours)
                    </h4>
                    <div className="space-y-3">
                      {suspiciousActivities.large_transactions.map((tx) => (
                        <div key={tx.transaction_id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                          <div>
                            <div className="font-medium">
                              {formatCurrency(tx.amount)}
                            </div>
                            <div className="text-sm text-gray-600">
                              User ID: {tx.user_id} • {tx.timestamp}
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            tx.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}>
                            {tx.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {suspiciousActivities.suspicious_users &&
                suspiciousActivities.suspicious_users.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-md font-medium text-gray-900 mb-4">
                      High Frequency Users (Last 24 Hours)
                    </h4>
                    <div className="space-y-3">
                      {suspiciousActivities.suspicious_users.map((user) => (
                        <div key={user.wallet_id} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                          <div>
                            <div className="font-medium">User ID: {user.user_id}</div>
                            <div className="text-sm text-gray-600">
                              {user.transaction_count} transactions • {formatCurrency(user.total_amount)}
                            </div>
                          </div>
                          <button className="px-3 py-1 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">
                            Investigate
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {suspiciousActivities.failed_logins &&
                suspiciousActivities.failed_logins.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-md font-medium text-gray-900 mb-4">
                      Failed Login Attempts
                    </h4>
                    <div className="space-y-2">
                      {suspiciousActivities.failed_logins.map((login, index) => (
                        <div key={index} className="text-sm text-gray-600">
                          <span className="font-medium">IP: {login.actor_ip}</span> • {login.timestamp}
                          {login.error_message && (
                            <div className="text-red-600">{login.error_message}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminAnalytics;