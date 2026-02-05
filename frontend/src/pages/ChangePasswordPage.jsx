import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { changePassword, clearUserMessages } from '../features/profileSlice';

export default function ChangePasswordPage() {
    const dispatch = useDispatch();
    const { status, error, success } = useSelector((state) => state.profile);

    const [formData, setFormData] = useState({
        current_password: "",
        new_password: "",
    });

    function handleChange(e){
        dispatch(clearUserMessages());
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    }

    function handleSubmit(e){
        e.preventDefault();
        dispatch(changePassword(formData));
    }

    return (
        <div className="mx-auto max-w-6xl px-4 py-6">

            <div className="mb-6">
                <h1 className="text-2xl font-bold text-slate-900">Change Password</h1>
                <p className="text-sm text-slate-600">
                    Update your account password(OTP required)
                    </p>
            </div>

            {/* Alerts */}
            {error && (
                <div className="mb-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
                    {error}
                </div>
            )}
            {success && (
                <div className="mb-4 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800">
                    {success}
                </div>
            )}

            <div className="max-w-md rounded-2xl border bg-white p-5 shadow-sm">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className='mb-1 block text-sm font-medium text-slate-700'>
                            Current Password
                        </label>
                        <input
                            type="password"
                            name="current_password"
                            value={formData.current_password}
                            onChange={handleChange}
                            placeholder='Enter current password'
                            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    <div>
                        <label className='mb-1 block text-sm font-medium text-slate-700'>
                            New Password
                        </label>
                        <input
                            type="password"
                            name="new_password"
                            value={formData.new_password}
                            onChange={handleChange}
                            placeholder='Enter new password'
                            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={status === "loading"}
                        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-blue-300"
                    >
                        {status === "loading" ? "Updating..." : "Update Password"}
                    </button>
                </form>
            </div>
        </div>
    );
}