import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { loadSystemStats } from '../../store/slices/adminAnalyticsSlice';
import StatsCard from '../../components/admin/StatsCard';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

const AdminDashboard = () => {
  const dispatch = useDispatch();
  const { systemStats, loading, error } = useSelector((state) => state.adminAnalytics);

  useEffect(() => {
    dispatch(loadSystemStats());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!systemStats) return null;

  const { users, wallets, transactions } = systemStats;

  // Prepare data for charts
  const userDistributionData = [
    { name: 'Active', value: users.active, color: '#10b981' },
    { name: 'Inactive', value: users.total - users.active, color: '#ef4444' },
  ];

  const kycStatusData = [
    { name: 'Verified', value: users.kyc_verified, color: '#10b981' },
    { name: 'Pending', value: users.kyc_pending, color: '#f59e0b' },
    { name: 'Rejected', value: users.kyc_rejected, color: '#ef4444' },
    { name: 'Not Started', value: users.total - users.kyc_verified - users.kyc_pending - users.kyc_rejected, color: '#6b7280' },
  ];

  const transactionMetrics = [
    { metric: 'Volume', today: transactions.today_volume, last30: transactions.volume_last_30_days / 30 },
    { metric: 'Count', today: transactions.today_count, last30: transactions.total_last_30_days / 30 },
    { metric: 'Fees', today: transactions.today_fees, last30: transactions.fees_last_30_days / 30 },
  ];

  const systemHealthData = [
    { subject: 'Users', value: (users.active / users.total) * 100, fullMark: 100 },
    { subject: 'KYC', value: (users.kyc_verified / users.total) * 100, fullMark: 100 },
    { subject: 'Transactions', value: (transactions.completed_last_30_days / transactions.total_last_30_days) * 100, fullMark: 100 },
    { subject: 'Wallets', value: wallets.total > 0 ? 95 : 0, fullMark: 100 },
    { subject: 'Revenue', value: transactions.fees_last_30_days > 1000 ? 85 : 50, fullMark: 100 },
  ];

  const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <button
          onClick={() => dispatch(loadSystemStats())}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Users"
          value={users.total}
          icon="👥"
          color="bg-blue-500"
        />
        <StatsCard
          title="Active Users"
          value={users.active}
          icon="✅"
          color="bg-green-500"
          subtitle={`${((users.active / users.total) * 100).toFixed(1)}% of total`}
        />
        <StatsCard
          title="Total Balance"
          value={`$${wallets.total_balance.toLocaleString()}`}
          icon="💵"
          color="bg-emerald-500"
        />
        <StatsCard
          title="Today's Revenue"
          value={`$${transactions.today_fees.toLocaleString()}`}
          icon="💰"
          color="bg-cyan-500"
        />
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* User Distribution Pie Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">User Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={userDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {userDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4 text-center">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{users.active}</p>
              <p className="text-sm text-gray-600">Active</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{users.total - users.active}</p>
              <p className="text-sm text-gray-600">Inactive</p>
            </div>
          </div>
        </div>

        {/* KYC Status Pie Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">KYC Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={kycStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => percent > 0 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {kycStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 bg-green-50 rounded">
              <p className="font-bold text-green-600">{users.kyc_verified}</p>
              <p className="text-gray-600">Verified</p>
            </div>
            <div className="p-2 bg-yellow-50 rounded">
              <p className="font-bold text-yellow-600">{users.kyc_pending}</p>
              <p className="text-gray-600">Pending</p>
            </div>
            <div className="p-2 bg-red-50 rounded">
              <p className="font-bold text-red-600">{users.kyc_rejected}</p>
              <p className="text-gray-600">Rejected</p>
            </div>
          </div>
        </div>

        {/* Transaction Comparison Bar Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Transaction Metrics: Today vs Avg (Last 30 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={transactionMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip formatter={(value) => `$${parseFloat(value).toFixed(2)}`} />
              <Legend />
              <Bar dataKey="today" fill="#6366f1" name="Today" />
              <Bar dataKey="last30" fill="#8b5cf6" name="30-Day Average" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* System Health Radar Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">System Health Overview</h2>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={systemHealthData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar
                name="Health Score"
                dataKey="value"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.6}
              />
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Wallet Analytics Area Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Wallet & Transaction Overview</h2>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart
            data={[
              { name: 'Wallets', value: wallets.total, category: 'count' },
              { name: 'Avg Balance', value: wallets.average_balance, category: 'amount' },
              { name: 'Total Balance', value: wallets.total_balance / 1000, category: 'amount' },
              { name: 'Today Txns', value: transactions.today_count, category: 'count' },
              { name: '30-Day Txns', value: transactions.total_last_30_days / 30, category: 'count' },
            ]}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip formatter={(value) => parseFloat(value).toFixed(2)} />
            <Legend />
            <Area type="monotone" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Revenue Insights with Gradient */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg shadow-md p-6 text-white">
        <h2 className="text-xl font-semibold mb-4">Revenue Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-indigo-200 text-sm mb-1">Total Fees (Last 30 Days)</p>
            <p className="text-3xl font-bold">
              ${transactions.fees_last_30_days.toLocaleString()}
            </p>
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm">📈</span>
              <span className="text-sm text-indigo-200">
                Avg: ${(transactions.fees_last_30_days / 30).toFixed(2)}/day
              </span>
            </div>
          </div>
          <div>
            <p className="text-indigo-200 text-sm mb-1">Completed Transactions</p>
            <p className="text-3xl font-bold">
              {transactions.completed_last_30_days.toLocaleString()}
            </p>
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm">✅</span>
              <span className="text-sm text-indigo-200">
                Success Rate: {((transactions.completed_last_30_days / transactions.total_last_30_days) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-indigo-200 text-sm mb-1">Average Fee per Transaction</p>
            <p className="text-3xl font-bold">
              $
              {transactions.completed_last_30_days > 0
                ? (transactions.fees_last_30_days / transactions.completed_last_30_days).toFixed(2)
                : '0.00'}
            </p>
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm">💎</span>
              <span className="text-sm text-indigo-200">
                Volume: ${transactions.volume_last_30_days.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
