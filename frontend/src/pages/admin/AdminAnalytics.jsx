import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  loadProfitTrends,
  setTrendsDays,
} from '../../store/slices/adminAnalyticsSlice';
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
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

const AdminAnalytics = () => {
  const dispatch = useDispatch();
  const { profitTrends, loading, error, trendsDays } = useSelector(
    (state) => state.adminAnalytics
  );

  useEffect(() => {
    dispatch(loadProfitTrends(trendsDays));
  }, [dispatch, trendsDays]);

  const handleDaysChange = (days) => {
    dispatch(setTrendsDays(days));
    dispatch(loadProfitTrends(days));
  };

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

  if (!profitTrends) return null;

  const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Analytics & Insights</h1>
        <div className="flex space-x-2">
          {[7, 30, 60, 90].map((days) => (
            <button
              key={days}
              onClick={() => handleDaysChange(days)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                trendsDays === days
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {days} Days
            </button>
          ))}
        </div>
      </div>

      {/* Daily Trends Chart - Enhanced with Area Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Revenue & Transaction Trends</h2>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={profitTrends.daily_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(date) => format(new Date(date), 'MMM dd')}
            />
            <YAxis yAxisId="left" label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
            <Tooltip
              labelFormatter={(date) => format(new Date(date), 'MMM dd, yyyy')}
              formatter={(value, name) => {
                if (name === 'Transaction Count') return [value, name];
                return [`$${parseFloat(value).toLocaleString()}`, name];
              }}
            />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="total_fees"
              fill="#6366f1"
              stroke="#6366f1"
              fillOpacity={0.3}
              name="Total Fees"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="transaction_count"
              stroke="#10b981"
              strokeWidth={3}
              name="Transaction Count"
              dot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Chart - Enhanced with Gradient */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Daily Transaction Volume</h2>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={profitTrends.daily_trends}>
            <defs>
              <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(date) => format(new Date(date), 'MMM dd')}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(date) => format(new Date(date), 'MMM dd, yyyy')}
              formatter={(value) => `$${parseFloat(value).toLocaleString()}`}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="total_volume" 
              stroke="#8b5cf6" 
              fillOpacity={1}
              fill="url(#colorVolume)"
              name="Total Volume" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction Type Distribution - Enhanced Donut Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Revenue by Transaction Type
          </h2>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={profitTrends.by_transaction_type}
                dataKey="total_fees"
                nameKey="type"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                labelLine={true}
              >
                {profitTrends.by_transaction_type.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value, name) => [`$${parseFloat(value).toFixed(2)}`, name]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {profitTrends.by_transaction_type.map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="text-sm font-medium text-gray-700">{item.type}</span>
                  </div>
                  <span className="text-xs font-semibold text-gray-500">{item.transaction_count}</span>
                </div>
                <p className="text-lg font-bold text-gray-900 mt-1">${item.total_fees.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Top Users - Enhanced with Progress Bars */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Top Revenue Generators</h2>
          <div className="space-y-3 max-h-[450px] overflow-y-auto">
            {profitTrends.top_users.slice(0, 10).map((user, index) => {
              const maxFees = profitTrends.top_users[0].total_fees;
              const percentage = (user.total_fees / maxFees) * 100;
              return (
                <div
                  key={user.user_id}
                  className="p-4 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                        index === 0 ? 'bg-yellow-500' :
                        index === 1 ? 'bg-gray-400' :
                        index === 2 ? 'bg-orange-600' :
                        'bg-gradient-to-br from-indigo-500 to-purple-600'
                      }`}>
                        {index < 3 ? ['🥇', '🥈', '🥉'][index] : index + 1}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{user.username}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-indigo-600">
                        ${user.total_fees.toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500">{user.transaction_count} txns</p>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-indigo-600 to-purple-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg shadow-md p-6 text-white">
        <h2 className="text-xl font-semibold mb-4">Period Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-indigo-200 text-sm mb-1">Total Revenue</p>
            <p className="text-3xl font-bold">
              $
              {profitTrends.daily_trends
                .reduce((sum, day) => sum + day.total_fees, 0)
                .toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-indigo-200 text-sm mb-1">Total Transactions</p>
            <p className="text-3xl font-bold">
              {profitTrends.daily_trends
                .reduce((sum, day) => sum + day.transaction_count, 0)
                .toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-indigo-200 text-sm mb-1">Total Volume</p>
            <p className="text-3xl font-bold">
              $
              {profitTrends.daily_trends
                .reduce((sum, day) => sum + day.total_volume, 0)
                .toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalytics;
