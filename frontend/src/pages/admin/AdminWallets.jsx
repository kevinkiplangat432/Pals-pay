import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import api from "../../services/api";
import LoadingSpinner from "../../components/common/LoadingSpinner";
import ErrorMessage from "../../components/common/ErrorMessage";
import EmptyState from "../../components/common/EmptyState";
import { loadWallets, setFilters } from "../../store/slices/adminWalletsSlice";

const AdminWallets = () => {
  const dispatch = useDispatch();
  const { wallets, loading, error, filters, total, pages, currentPage } = useSelector(
    (state) => state.adminWallets
  );

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedWallet, setSelectedWallet] = useState(null);

  useEffect(() => {
    dispatch(loadWallets(filters));
  }, [dispatch, filters]);

  const handleSearch = (e) => {
    e.preventDefault();
    dispatch(setFilters({ search: searchTerm, page: 1 }));
  };

  const handleFreezeToggle = async (walletId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'frozen' : 'active';
    try {
      await api.put(`/admin/wallets/${walletId}/status`, { status: newStatus });
      dispatch(loadWallets(filters));
    } catch (error) {
      console.error('Failed to update wallet status:', error);
    }
  };

  const handlePageChange = (page) => {
    dispatch(setFilters({ page }));
  };

  const formatCurrency = (amount, currency = "KES") => {
    return new Intl.NumberFormat("en-KE", {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Wallet Management</h1>
        <div className="text-sm text-gray-600">
          <span className="font-medium">{total}</span> wallets •{" "}
          <span className="font-medium">
            {wallets.reduce((sum, w) => sum + (parseFloat(w.balance) || 0), 0).toLocaleString()} KES
          </span>{" "}
          total balance
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            placeholder="Search by user email, phone, or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex gap-4 mt-4">
          <select
            value={filters.status || ""}
            onChange={(e) => dispatch(setFilters({ status: e.target.value || "", page: 1 }))}
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="frozen">Frozen</option>
            <option value="suspended">Suspended</option>
          </select>

          <input
            type="number"
            placeholder="Min Balance"
            value={filters.min_balance || ""}
            onChange={(e) => dispatch(setFilters({ min_balance: e.target.value, page: 1 }))}
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 w-40"
          />
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading ? (
        <LoadingSpinner />
      ) : wallets.length === 0 ? (
        <EmptyState
          icon="wallet"
          title="No Wallets Found"
          message="Try adjusting your search criteria"
        />
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Wallet Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Limits
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {wallets.map((wallet) => (
                  <tr key={wallet.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                          <span className="text-green-600 font-bold">
                            {wallet.user?.first_name?.[0] || "U"}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {wallet.user?.first_name} {wallet.user?.last_name}
                          </div>
                          <div className="text-sm text-gray-500">{wallet.user?.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">ID: {wallet.id}</div>
                      <div className="text-sm text-gray-500">Currency: {wallet.currency || "KES"}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-lg font-bold text-gray-900">
                        {formatCurrency(wallet.balance, wallet.currency)}
                      </div>
                      <div className="text-sm text-gray-500">
                        Available: {formatCurrency(wallet.available_balance, wallet.currency)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm">
                        <div>Daily: {formatCurrency(wallet.daily_limit, wallet.currency)}</div>
                        <div>Monthly: {formatCurrency(wallet.monthly_limit, wallet.currency)}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          wallet.status === "active"
                            ? "bg-green-100 text-green-800"
                            : wallet.status === "frozen"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {wallet.status || "active"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        onClick={() => setSelectedWallet(wallet)}
                        className="text-green-600 hover:text-green-900 mr-3"
                      >
                        View Details
                      </button>
                      <button 
                        onClick={() => handleFreezeToggle(wallet.id, wallet.status || 'active')}
                        className="text-red-600 hover:text-red-900"
                      >
                        {(wallet.status || 'active') === "active" ? "Freeze" : "Unfreeze"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Page <span className="font-medium">{currentPage}</span> of{" "}
                <span className="font-medium">{pages}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= pages}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedWallet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedWallet(null)}>
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">Wallet Details</h2>
              <button onClick={() => setSelectedWallet(null)} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div><span className="font-semibold">Wallet ID:</span> {selectedWallet.id}</div>
                <div><span className="font-semibold">Currency:</span> {selectedWallet.currency || 'KES'}</div>
                <div><span className="font-semibold">User:</span> {selectedWallet.user?.first_name} {selectedWallet.user?.last_name}</div>
                <div><span className="font-semibold">Email:</span> {selectedWallet.user?.email}</div>
                <div><span className="font-semibold">Balance:</span> {formatCurrency(selectedWallet.balance, selectedWallet.currency)}</div>
                <div><span className="font-semibold">Available:</span> {formatCurrency(selectedWallet.available_balance, selectedWallet.currency)}</div>
                <div><span className="font-semibold">Daily Limit:</span> {formatCurrency(selectedWallet.daily_limit, selectedWallet.currency)}</div>
                <div><span className="font-semibold">Monthly Limit:</span> {formatCurrency(selectedWallet.monthly_limit, selectedWallet.currency)}</div>
                <div><span className="font-semibold">Status:</span> <span className={`px-2 py-1 rounded text-xs ${(selectedWallet.status || 'active') === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{selectedWallet.status || 'active'}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminWallets;