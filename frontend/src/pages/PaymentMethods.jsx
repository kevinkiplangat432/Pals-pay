import React, { useEffect, useState} from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  addPaymentMethod,
  deletePaymentMethod,
 fetchPaymentMethods,
 setDefaultPaymentMethod,
 verifyPaymentMethod,
 clearPaymentMethodMessages,
} from "../features/paymentMethodsSlice";

export default function PaymentMethodsPage() {
    const dispatch = useDispatch();
    const { items, status, error, success } = useSelector((s) => s.paymentMethods);

    const [form, setForm] = useState({
        provider: "",
        account_reference: "",
        account_name: "",
        is_default: false,
    });

    const [verify, setVerify] = useState({
        Id: "",
        verification_token: "",
    });

    useEffect(() => {
        dispatch(fetchPaymentMethods());
    }, [dispatch]);

    function handleChange(e) {
        dispatch(clearPaymentMethodMessages());
        const { name, value, type, checked } = e.target;

        setForm((prev) => ({
            ...prev,
            [name]: type === "checkbox" ? checked : value,
        }));
    }

    function onVerifyChange(e) {
        const { name, value } = e.target;

        setVerify((prev) => ({
            ...prev,
            [name]: value,
        }));
    }

    async function onAdd(e) {
        e.preventDefault();
        const res = await dispatch(addPaymentMethod(form));
        if (addPaymentMethod.fulfilled.match(res)) {
            setForm({
                provider: "",
                account_reference: "",
                account_name: "",
                is_default: false,
            });
            dispatch(fetchPaymentMethods());
        }
    }

    async function onVerify(e) {
        e.preventDefault();
        const res = await dispatch(verifyPaymentMethod({
            id: verify.Id,
            verification_token: verify.verification_token,
        }));
        if (verifyPaymentMethod.fulfilled.match(res)) {
            setVerify({
                Id: "",
                verification_token: "",
            });
            dispatch(fetchPaymentMethods());
        }
    }

    return(
        <div className="mx-auto max-w-6xl px-4 py-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-slate-900">Payment Methods</h1>
                <p className="text-sm text-slate-600">
                    Manage your payment methods
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

            {status === "loading" && (
                <div className="text-sm text-slate-600">Loading...</div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                    <h2 className="mb-3 text-sm font-semibold text-slate-700">
                        Add Payment Method
                    </h2>

                    <form onSubmit={onAdd} className="space-y-4">
                        <div>
                           <label className="mb-1 block text-sm font-medium text-slate-700">
                                Provider
                            </label>
                            <select
                                name="provider"
                                value={form.provider}
                                onChange={handleChange}
                                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300"
                            >
                                <option value="mpesa">M-Pesa</option>
                                <option value="card">Card</option>
                                <option value="Bank">Bank</option>
                            </select>
                        </div>

                        <div>
                            <label className="mb-1 block text-sm font-medium text-slate-700">
                                Account Reference
                            </label>
                            <input
                                name="account_reference"
                                value={form.account_reference}
                                onChange={handleChange}
                                placeholder="phone number, card number or account number"
                                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300"
                            />
                        </div>

                        <div>
                            <label className="mb-1 block text-sm font-medium text-slate-700">
                                Account Name (optional)
                            </label>
                            <input
                                name="account_name"
                                value={form.account_name}
                                onChange={handleChange}
                                placeholder="Account holder name"
                                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300"
                            />
                        </div>

                        <label className="flex items-center gap-2 text-sm text-slate-700">
                            <input
                                type="checkbox"
                                name="is_default"
                                checked={form.is_default}
                                onChange={handleChange}
                                className="h-4 w-4 rounded border-slate-300 "
                            />
                            Set as default
                        </label>

                        <button type="submit" className="rounded-xl bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                            Add Payment Method
                        </button>
                    </form>
                </div>

                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                    <h2 className="mb-3 text-sm font-semibold text-slate-700">
                        Verify Payment Method
                    </h2>

                    <form onSubmit={onVerify} className="space-y-4">
                        <input
                            name="Id"
                            value={verify.Id}
                            onChange={onVerifyChange}
                            placeholder="Payment Method Id"
                            className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300"
                        />
                        
                        <input
                            name="verification_token"
                            value={verify.verification_token}
                            onChange={onVerifyChange}
                            placeholder="Verification Token"
                            className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring-slate-300"
                        />

                        <button type="submit" className="w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
                            Verify Payment Method
                        </button>
                    </form>
                </div>
            </div>

            <div className="mt-8 grid gap-4">
                {items.map((method) => (
                    <div key={method.id} 
                    className="rounded-2xl border bg-white p-5 shadow-sm ">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <div className="text-sm font-bold text-slate-900">
                                    {method.provider}
                                    {method.is_default && (
                                        <span className="ml-2 rounded-full bg-slate-900 px-2 py-0.5 text-xs text-white">
                                            default
                                        </span>
                                    )}
                                </div>
                                <div className="mt-1 text-xs text-slate-600">
                                    {method.account_reference}
                                </div>
                                {method.account_name && (
                                    <div className="text-xs text-slate-600">
                                        {method.account_name}
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-2">
                                {!method.is_default && (
                                    <button
                                    onClick={async () => {
                                        await dispatch(setDefaultPaymentMethod(method.id));
                                        dispatch(fetchPaymentMethods());
                                    }}
                                    className="rounded-xl border px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                                    >
                                        Set Default
                                    </button>
                                )}

                                <button
                                    onClick={async () => {
                                        await dispatch(deletePaymentMethod(method.id));
                                        dispatch(fetchPaymentMethods());
                                    }}
                                    className="rounded-xl border px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

}