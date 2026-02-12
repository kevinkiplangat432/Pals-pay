import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  clearUserMessages,
  fetchKycStatus,
  submitKycDocuments,
} from "../features/profileSlice";
import PageWithLogo from "../components/common/PageWithLogo";

export default function KycPage() {
  const dispatch = useDispatch();
  const { kyc, status, error, success } = useSelector((s) => s.user);

  const [form, setForm] = useState({
    document_type: "",
    document_number: "",
    front_document: null,
    back_document: null,
    selfie: null,
  });


  useEffect(() => {
    dispatch(fetchKycStatus());
  }, [dispatch]);

  function handleChange(e) {
    dispatch(clearUserMessages());
    const { name, value, files } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: files ? files[0] : value,
    }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    dispatch(submitKycDocuments(form));
  }

  return (
    <PageWithLogo>
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">KYC Verification</h1>
        <p className="text-sm text-slate-600">
          Submit identity documents for verification
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
    
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Current Kyc Status
          </h2>

          {kyc ? (
            <div className="space-y-2 text-sm text-slate-700">
              <div>
                <span className="font-semibold">Status:</span>{" "}
                {kyc.status ?? "unknown"}
              </div>
              <div>
                <span className="font-semibold">Submitted:</span>{" "}
                {kyc.submitted ? "Yes" : "No"}
              </div>
              {"is_expired" in kyc && (
                <div>
                  <span className="font-semibold">Expired:</span>{" "}
                  {kyc.is_expired ? "Yes" : "No"}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-600">No KYC data available</p>
          )}

          <button
            onClick={() => dispatch(fetchKycStatus())}
            className="mt-4 rounded-xl border px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Refresh Status
          </button>
        </div>

        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Submit Documents
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Document Type
              </label>
              <input
                name="document_type"
                value={form.document_type}
                onChange={handleChange}
                placeholder="e.g. national_id, passport"
                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Document Number
              </label>
              <input
                name="document_number"
                value={form.document_number}
                onChange={handleChange}
                placeholder="Document number"
                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Front Document (required)
              </label>
              <input
                type="file"
                name="front_document"
                onChange={handleChange}
                className="block w-full text-sm text-slate-700"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Back Document (optional)
              </label>
              <input
                type="file"
                name="back_document"
                onChange={handleChange}
                className="block w-full text-sm text-slate-700"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Selfie (optional)
              </label>
              <input
                type="file"
                name="selfie"
                onChange={handleChange}
                className="block w-full text-sm text-slate-700"
              />
            </div>

            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
            >
              {status === "loading" ? "Submitting…" : "Submit KYC"}
            </button>
          </form>
        </div>
      </div>
    </div>
    </PageWithLogo>
  );
}
