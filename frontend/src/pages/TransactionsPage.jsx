import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchTransactions } from "../features/transactionsSlice";

export default function TransactionsPage() {
  const dispatch = useDispatch();
  const { data, status, error } = useSelector((s) => s.transactions);

  const [page, setPage] = useState(1);
  const [type, setType] = useState("");

  useEffect(() => {
    dispatch(
        fetchTransactions({ 
            page,
            per_page: 20, 
            type: type || undefined,
        })
    );
  }, [dispatch, page, type]);

  const transactions = data?.transactions || data?.items || data?.data || [];

  return(
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Transactions</h1>
        <p className="text-sm text-slate-600">
          View your transaction history
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {status === "loading" && (
        <div className=" mb-4 text-sm text-slate-600">Loading transactions...</div>
        )}

        <div className="mb-6 flex flex-wrap items-center gap-4">
            <div>
                <label className="mr-2 text-sm font-medium text-slate-700">
                    Filter by Type
                </label>
                <select
                value={type}
                onChange={(e) => {
                    setPage(1);
                    setType(e.target.value);
                }}
                className="rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                >
                <option value="">All</option>
                <option value="deposit">Deposit</option>
                <option value="transfer">Transfer</option>
                <option value="withdrawal">Withdrawal</option>
                </select>
            </div>

            <div className="ml-auto flex items-center gap-2">
                <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="rounded-xl border px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                Previous
                </button>
                <span className="text-sm text-slate-600">Page {page}</span>
                <button
                onClick={() => setPage((p) => p + 1)}
                className="rounded-xl border px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                Next
                </button>
              </div>
            </div>

            <div className="grid gap-4">
                {transactions.length === 0 && status !== "loading" && (
                    <div className="rounded-xl border bg-white px-4 py-6 text-center text-sm text-slate-600">
                        No transactions found
                    </div>
                )}

                {transactions.map((tx) => (
                    <div key={tx.id} 
                    className="rounded-xl border bg-white p-4 shadow-sm"
                >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <div className="text-sm font-bold text-slate-900">
                                    {tx.transaction_type || tx.type }
                                </div>
                                <div className="mt-1 text-xs text-slate-600">
                                    {tx.created_at || ""}
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-bold text-slate-900">
                                    {tx.amount}
                                </div>
                                <div className="text-xs text-slate-600">
                                    {tx.status}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
  )

}