import React, { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
    clearWalletMessages,
    depositMpesa,
    fetchWalletAnalytics, 
    fetchWalletSummary, 
    fetchTransactionSummary, 
    transferToBeneficiaryWallet,
    transferToPhone,
    withdrawFunds,
 } from '../features/walletSlice';

export default function WalletPage() {
    const dispatch = useDispatch();
    const { analytics, summary, transactionSummary, status, error, success } = useSelector((s) => s.wallet || {});

    const [days, setDays] = useState(30);

    const [depositForm, setDepositForm] = useState({
        amount: "",
        phone_number: "",
    });

    const [transferPhoneForm, setTransferPhoneForm] = useState({
        phone_number: "",
        amount: "",
        description: "",
    });

    const [transferWalletForm, setTransferWalletForm] = useState({
        beneficiary_wallet_id: "",
        amount: "",
        description: "",
    });

    const [withdrawForm, setWithdrawForm] = useState({
        amount: "",
        payment_method_id: "",
    });

    useEffect(() => {
        dispatch(fetchWalletSummary());
        dispatch(fetchWalletAnalytics());
        dispatch(fetchTransactionSummary({ days: 30 }));
    }, [dispatch]);

    const isLoading = status === "loading";

    const balanceText = useMemo(() => {
        if (!summary) return "--";

        const bal =
          summary.balance ??
          summary.current_balance ??
          summary.available_balance ??
          summary.wallet_balance;

        const currency = summary.currency || "USD";
        return  bal !== undefined ? `${bal} ${currency}` : "--";
    }, [summary]);

    function resetMessages() {
        dispatch(clearWalletMessages());
    }

    async function onRefreshAll() {
        resetMessages();
        dispatch(fetchWalletSummary());
        dispatch(fetchWalletAnalytics());
        dispatch(fetchTransactionSummary({ days }));
    }

    async function onDeposit(e) {
        e.preventDefault();
        resetMessages();
    

    const amount = Number(depositForm.amount);
    const phone_number = depositForm.phone_number.trim();

    if (!amount || amount <= 0) return;

    const res = await dispatch(depositMpesa({ amount, phone_number }));
    if (depositMpesa.fulfilled.match(res)) {
        setDepositForm({ amount: "", phone_number: "" });
        dispatch(fetchWalletSummary());
        dispatch(fetchTransactionSummary({ days }));
    }
}


    async function onTransferWallet(e) {
        e.preventDefault();
        resetMessages();

        const beneficiary_wallet_id = Number(transferWalletForm.beneficiary_wallet_id);
        const amount = Number(transferWalletForm.amount);

        if (!beneficiary_wallet_id || !amount || amount <= 0) return;

        const res = await dispatch(
          transferToBeneficiaryWallet({
            beneficiary_wallet_id, 
            amount, 
            description: transferWalletForm.description || undefined}
        ));

        if (transferToBeneficiaryWallet.fulfilled.match(res)) {
            setTransferWalletForm({ beneficiary_wallet_id: "", amount: "", description: "" });
            dispatch(fetchWalletSummary());
            dispatch(fetchWalletAnalytics());
            dispatch(fetchTransactionSummary({ days }));
        }
    }

    async function onTransferPhone(e) {
        e.preventDefault();
        resetMessages();

        const phone_number = transferPhoneForm.phone_number.trim();
        const amount = Number(transferPhoneForm.amount);

        if (!phone_number || !amount || amount <= 0) return;

        const res = await dispatch(
          transferToPhone({
            phone_number, 
            amount, 
            description: transferPhoneForm.description || undefined}
        ));

        if (transferToPhone.fulfilled.match(res)) {
            setTransferPhoneForm({ phone_number: "", amount: "", description: "" });
            dispatch(fetchWalletSummary());
            dispatch(fetchWalletAnalytics());
            dispatch(fetchTransactionSummary({ days }));
        }
    }

    async function onWithdraw(e) {
        e.preventDefault();
        resetMessages();

        const amount = Number(withdrawForm.amount);
        const payment_method_id = Number(withdrawForm.payment_method_id);

        if (!amount || amount <= 0 || !payment_method_id) return;

        const res = await dispatch(
          withdrawFunds({
            amount, 
            payment_method_id, 
          })
        );

        if (withdrawFunds.fulfilled.match(res)) {
            setWithdrawForm({ amount: "", payment_method_id: "" });
            dispatch(fetchWalletSummary());
            dispatch(fetchWalletAnalytics());
            dispatch(fetchTransactionSummary({ days }));
        }
    }

    return (
        <div className='mx-auto max-w-6xl px-4 py-6'>
            <div className='mb-6 flex flex-wrap items-end justify-between gap-3'>
                <div>
                    <h1 className='text-2xl font-bold text-slate-900'>Wallet</h1>
                    <p className='text-sm text-slate-600'>
                        View your wallet balance, analytics and recent transactions
                    </p>
                </div>

                <button 
                    onClick={onRefreshAll}
                    className='rounded-xl border px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50'
                >
                    Refresh
                </button>
            </div>

            {error && (
                <div className='mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'>
                    {error}
                </div>
            )}

            {success && (
                <div className='mb-4 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700'>
                    {success}
                </div>
            )}

            {isLoading && (
                <p className='mb-4 text-sm text-slate-600'>Loading...</p>
            )}

            <div className='grid gap-4 md:grid-cols-3'>
                <div className='rounded-2xl border bg-white p-5 shadow-sm'>
                    <div className='text-sm font-semibold text-slate-700'>Current Balance</div>
                    <div className='mt-2 text-2xl font-bold text-slate-900'>{balanceText}</div>
                    
                </div>
                <div className='rounded-2xl border bg-white p-5 shadow-sm md:col-span-2'>
                    <div className='text-sm font-semibold text-slate-700'>Wallet Analytics (Last 30 days)</div>
                    <pre className='mt-3 max-h-56 overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-700'>
                        {analytics ? JSON.stringify(analytics, null, 2) : "--"}
                    </pre>
                    <div className='mt-4 text-sm font-semibold text-slate-700'>
                        Transaction Summary
                    </div>
                    

                    <div className='flex items-center gap-2'>
                        <label className='text-sm text-slate-700'>Days</label>
                        <input
                            value={days}
                            onChange={(e) => setDays(Number(e.target.value || 30))}
                            className='w-24 rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            placeholder='30'
                        />
                        <button
                            onClick={() => {
                                resetMessages();
                                dispatch(fetchTransactionSummary({ days }));
                            }}
                            className='rounded-xl border px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50'
                            >
                                Load
                                </button>
                            </div>
                        </div>
                    <pre className='mt-3 max-h-56 overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-700'>
                        {transactionSummary ? JSON.stringify(transactionSummary, null, 2) : "--"}
                    </pre>
                </div>

                <div className='mt-6 grid gap-6 lg:grid-cols-2'>
                    <div className='rounded-2xl border bg-white p-5 shadow-sm'>
                        <h2 className='text-sm font-semibold text-slate-700'>
                            Deposit via Mpesa
                        </h2>
                        
                        <form onSubmit={onDeposit} className='mt-4 space-y-3'>
                            <input
                                value={depositForm.amount}
                                onChange={(e) => setDepositForm((f) => ({ ...f, amount: e.target.value }))}
                                placeholder='Amount'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={depositForm.phone_number}
                                onChange={(e) => setDepositForm((f) => ({ ...f, phone_number: e.target.value }))}
                                placeholder='Phone number'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <button
                                type='submit'
                                disabled={isLoading}
                                className='w-full rounded-xl border px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50'
                            >
                                {isLoading ? "Processing..." : "Deposit"}
                            </button>
                        </form>
                    </div>
                    <div className='rounded-2xl border bg-white p-5 shadow-sm'>
                        <h2 className='text-sm font-semibold text-slate-700'>
                            Withdraw
                        </h2>

                        <form onSubmit={onWithdraw} className='mt-4 space-y-3'>
                            <input
                                value={withdrawForm.amount}
                                onChange={(e) => setWithdrawForm((f) => ({ ...f, amount: e.target.value }))}
                                placeholder='Amount'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={withdrawForm.payment_method_id}
                                onChange={(e) => setWithdrawForm((f) => ({ ...f, payment_method_id: e.target.value }))}
                                placeholder='Payment Method ID (verified)'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <button
                                type='submit'
                                disabled={isLoading}
                                className='w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60'
                            >
                                {isLoading ? "Processing..." : "Withdraw"}
                            </button>
                        </form>
                        </div>

                        <div className='rounded-2xl border bg-white p-5 shadow-sm'>
                        <h2 className='text-sm font-semibold text-slate-700'>
                            Transfer to beneficiary wallet
                        </h2>
                        <form onSubmit={onTransferWallet} className='mt-4 space-y-3'>
                            <input
                                value={transferWalletForm.beneficiary_wallet_id}
                                onChange={(e) => setTransferWalletForm((f) => ({ ...f, beneficiary_wallet_id: e.target.value }))}
                                placeholder='Beneficiary Wallet ID'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={transferWalletForm.amount}
                                onChange={(e) => setTransferWalletForm((f) => ({ ...f, amount: e.target.value }))}
                                placeholder='Amount'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={transferWalletForm.description}
                                onChange={(e) => setTransferWalletForm((f) => ({ ...f, description: e.target.value }))}
                                placeholder='Description (optional)'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <button
                                type='submit'
                                disabled={isLoading}
                                className='w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60'
                            >
                                {isLoading ? "Processing..." : " Send Transfer"}
                            </button>
                        </form>
                    </div>

                    <div className='rounded-2xl border bg-white p-5 shadow-sm'>
                        <h2 className='text-sm font-semibold text-slate-700'>
                            Transfer to phone number
                        </h2>
                        <form onSubmit={onTransferPhone} className='mt-4 space-y-3'>
                            <input
                                value={transferPhoneForm.phone_number}
                                onChange={(e) => setTransferPhoneForm((f) => ({ ...f, phone_number: e.target.value }))}
                                placeholder='Phone number (+254...)'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={transferPhoneForm.amount}
                                onChange={(e) => setTransferPhoneForm((f) => ({ ...f, amount: e.target.value }))}
                                placeholder='Amount'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <input
                                value={transferPhoneForm.description}
                                onChange={(e) => setTransferPhoneForm((f) => ({ ...f, description: e.target.value }))}
                                placeholder='Description (optional)'
                                className='w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300'
                            />
                            <button
                                type='submit'
                                disabled={isLoading}
                                className='w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60'
                            >
                                {isLoading ? "Processing..." : " Send Transfer"}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
    );
}

                    
    
        
    

