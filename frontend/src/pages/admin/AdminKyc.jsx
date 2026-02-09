import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import LoadingSpinner from "../../components/common/LoadingSpinner";
import ErrorMessage from "../../components/common/ErrorMessage";
import EmptyState from "../../components/common/EmptyState";
import { loadPendingKyc, verifyKycAction } from "../../store/slices/adminKycSlice";

const AdminKyc = () => {
  const dispatch = useDispatch();
  const { kycVerifications, loading, error, total, pages, currentPage } = useSelector(
    (state) => state.adminKyc
  );

  const [rejectionReason, setRejectionReason] = useState("");
  const [selectedKyc, setSelectedKyc] = useState(null);

  useEffect(() => {
    dispatch(loadPendingKyc());
  }, [dispatch]);

  const handleApprove = async (kycId) => {
    await dispatch(verifyKycAction({ kycId, approved: true }));
  };

  const handleReject = async (kycId) => {
    if (!rejectionReason.trim()) {
      alert("Please provide a rejection reason");
      return;
    }
    await dispatch(verifyKycAction({ kycId, approved: false, rejectionReason }));
    setRejectionReason("");
    setSelectedKyc(null);
  };

  const openRejectModal = (kyc) => {
    setSelectedKyc(kyc);
    setRejectionReason("");
  };

  const closeModal = () => {
    setSelectedKyc(null);
    setRejectionReason("");
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">KYC Verification</h1>
        <span className="text-sm text-gray-600">{total} pending verifications</span>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading ? (
        <LoadingSpinner />
      ) : kycVerifications.length === 0 ? (
        <EmptyState
          icon="✅"
          title="No Pending KYC Verifications"
          message="All KYC submissions have been processed"
        />
      ) : (
        <div className="grid gap-6">
          {kycVerifications.map((kyc) => (
            <div key={kyc.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {kyc.user?.first_name} {kyc.user?.last_name}
                  </h3>
                  <p className="text-sm text-gray-600">{kyc.user?.email}</p>
                  <p className="text-sm text-gray-600">{kyc.user?.phone_number}</p>
                </div>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                  {kyc.document_type || "Document"}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Document Details</h4>
                  <p className="text-sm text-gray-600">
                    Number: {kyc.document_number || "N/A"}
                  </p>
                  <p className="text-sm text-gray-600">
                    Submitted: {new Date(kyc.submitted_at).toLocaleDateString()}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Documents</h4>
                  <div className="flex gap-2">
                    {kyc.document_front_url && (
                      <a
                        href={kyc.document_front_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-900"
                      >
                        Front
                      </a>
                    )}
                    {kyc.document_back_url && (
                      <a
                        href={kyc.document_back_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-900"
                      >
                        Back
                      </a>
                    )}
                    {kyc.selfie_url && (
                      <a
                        href={kyc.selfie_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-900"
                      >
                        Selfie
                      </a>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => handleApprove(kyc.id)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => openRejectModal(kyc)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Reject
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                  Request More Info
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Rejection Modal */}
      {selectedKyc && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Reject KYC - {selectedKyc.user?.first_name} {selectedKyc.user?.last_name}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Please provide a reason for rejecting this KYC submission.
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Enter rejection reason..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-red-500 focus:border-transparent mb-4"
              rows={4}
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={closeModal}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleReject(selectedKyc.id)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Confirm Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminKyc;