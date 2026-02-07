import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { loadPendingKyc, verifyKycAction } from '../../store/slices/adminKycSlice';
import { format } from 'date-fns';

const AdminKyc = () => {
  const dispatch = useDispatch();
  const { kycVerifications, total, pages, currentPage, loading, error } = useSelector(
    (state) => state.adminKyc
  );

  const [selectedKyc, setSelectedKyc] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  useEffect(() => {
    dispatch(loadPendingKyc());
  }, [dispatch]);

  const handleApprove = async (kycId) => {
    if (window.confirm('Are you sure you want to approve this KYC verification?')) {
      await dispatch(verifyKycAction({ kycId, approved: true }));
      setSelectedKyc(null);
    }
  };

  const handleReject = async (kycId) => {
    if (!rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }
    if (window.confirm('Are you sure you want to reject this KYC verification?')) {
      await dispatch(
        verifyKycAction({ kycId, approved: false, rejectionReason: rejectionReason })
      );
      setSelectedKyc(null);
      setRejectionReason('');
    }
  };

  const viewDetails = (kyc) => {
    setSelectedKyc(kyc);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">KYC Verification</h1>
        <div className="text-sm text-gray-600">
          Pending Verifications: <span className="font-semibold">{total}</span>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* KYC Grid */}
      {loading ? (
        <div className="flex items-center justify-center p-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {kycVerifications.map((kyc) => (
            <div
              key={kyc.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                    {kyc.user?.username?.[0]?.toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {kyc.user?.first_name} {kyc.user?.last_name}
                    </h3>
                    <p className="text-sm text-gray-500">{kyc.user?.email}</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">
                  PENDING
                </span>
              </div>

              <div className="space-y-3 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Document Type:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {kyc.document_type?.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Document Number:</span>
                  <span className="text-sm font-mono text-gray-900">{kyc.document_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Submitted:</span>
                  <span className="text-sm text-gray-900">
                    {format(new Date(kyc.created_at), 'MMM dd, yyyy HH:mm')}
                  </span>
                </div>
              </div>

              {kyc.document_front_url && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Document Front:</p>
                  <img
                    src={kyc.document_front_url}
                    alt="Document Front"
                    className="w-full h-48 object-cover rounded-lg border border-gray-200"
                  />
                </div>
              )}

              {kyc.document_back_url && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Document Back:</p>
                  <img
                    src={kyc.document_back_url}
                    alt="Document Back"
                    className="w-full h-48 object-cover rounded-lg border border-gray-200"
                  />
                </div>
              )}

              {selectedKyc?.id === kyc.id && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rejection Reason (optional):
                  </label>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter reason for rejection..."
                  />
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => handleApprove(kyc.id)}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  Approve
                </button>
                {selectedKyc?.id === kyc.id ? (
                  <>
                    <button
                      onClick={() => handleReject(kyc.id)}
                      className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                    >
                      Confirm Reject
                    </button>
                    <button
                      onClick={() => {
                        setSelectedKyc(null);
                        setRejectionReason('');
                      }}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors font-medium"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => viewDetails(kyc)}
                    className="flex-1 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium"
                  >
                    Reject
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && kycVerifications.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">All Caught Up!</h3>
          <p className="text-gray-600">No pending KYC verifications at the moment.</p>
        </div>
      )}
    </div>
  );
};

export default AdminKyc;
