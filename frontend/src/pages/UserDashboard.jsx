import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchWalletSummary } from '../features/walletSlice';
import { fetchTransactions } from '../features/transactionsSlice';
import { Link } from 'react-router-dom';
import PageWithLogo from '../components/common/PageWithLogo';

const UserDashboard = () => {
  const dispatch = useDispatch();
  const wallet = useSelector((s) => s.wallet);
  const transactions = useSelector((s) => s.transactions);
  
  const summary = wallet?.summary;
  const data = transactions?.data;

  useEffect(() => {
    dispatch(fetchWalletSummary());
    dispatch(fetchTransactions({ page: 1, per_page: 5 }));
  }, [dispatch]);

  const txList = data?.transactions || data?.items || data?.data || [];
  const balance = summary?.balance ?? summary?.current_balance ?? summary?.available_balance ?? 0;
  const currency = summary?.currency || 'KES';

  return (
    <PageWithLogo>
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Wallet Balance</p>
              <p className="text-3xl font-bold text-gray-900">{balance} {currency}</p>
            </div>
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Total Transactions</p>
              <p className="text-3xl font-bold text-gray-900">{txList.length}</p>
            </div>
            <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Quick Actions</p>
              <Link to="/wallet" className="text-green-600 hover:text-green-700 font-medium">
                Send Money →
              </Link>
            </div>
            <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
          <Link to="/transactions" className="text-green-600 hover:text-green-700 text-sm font-medium">
            View All
          </Link>
        </div>

        {txList.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No transactions yet</p>
        ) : (
          <div className="space-y-3">
            {txList.slice(0, 5).map((tx) => (
              <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{tx.transaction_type || tx.type}</p>
                  <p className="text-xs text-gray-500">{tx.created_at}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">{tx.amount}</p>
                  <p className="text-xs text-gray-500">{tx.status}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
    </PageWithLogo>
  );
};

export default UserDashboard;
