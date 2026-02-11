import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import StatsCard from "../../components/admin/StatsCard";
import LoadingSpinner from "../../components/common/LoadingSpinner";
import ErrorMessage from "../../components/common/ErrorMessage";
import { loadSystemStats } from "../../store/slices/adminAnalyticsSlice";

const AdminDashboard = () => {
  const dispatch = useDispatch();
  const { systemStats, loading, error } = useSelector(
    (state) => state.adminAnalytics
  );

  useEffect(() => {
    dispatch(loadSystemStats());
  }, [dispatch]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  const stats = systemStats?.users || {};

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Users"
          value={stats.total || 0}
          icon="users"
          color="bg-blue-100"
          subtitle={`${stats.active || 0} active`}
        />
        <StatsCard
          title="Today's Transactions"
          value={systemStats?.transactions?.today_count || 0}
          icon="dollar"
          color="bg-green-100"
          subtitle={`KES ${systemStats?.transactions?.today_volume || 0}`}
        />
        <StatsCard
          title="KYC Verified"
          value={stats.kyc_verified || 0}
          icon="check"
          color="bg-purple-100"
          subtitle={`${stats.kyc_pending || 0} pending`}
        />
        <StatsCard
          title="Total Balance"
          value={`KES ${systemStats?.wallets?.total_balance || 0}`}
          icon="wallet"
          color="bg-yellow-100"
          subtitle={`${systemStats?.wallets?.total || 0} wallets`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Activity
          </h2>
          {/* Add activity list here */}
          <p className="text-gray-500">No recent activity</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            System Status
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">API Status</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Database</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Payment Gateway</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;