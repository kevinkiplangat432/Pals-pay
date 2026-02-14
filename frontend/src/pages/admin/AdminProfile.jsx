import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { clearUserMessages, fetchUserProfile, updateUserProfile} from '../../features/profileSlice';

export default function AdminProfile() {
    const dispatch = useDispatch();
    const { profile, status, error, success } = useSelector((state) => state.user);

    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        phone_number: "",
        date_of_birth: "",
    });

    useEffect(() => {
        dispatch(fetchUserProfile());
    }, [dispatch]);

    useEffect(() => {
        if (profile) {
            setFormData({
                first_name: profile.first_name || "",
                last_name: profile.last_name || "",
                phone_number: profile.phone_number || "",
                date_of_birth: profile.date_of_birth || "",
            });
        }
    }, [profile]);

    const handleChange = (e) => {
        dispatch(clearUserMessages());
        const { name, value, type, checked } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    function handleSubmit(e){
        e.preventDefault();
        dispatch(updateUserProfile(formData));
    }

    return (
        <div className="mx-auto max-w-6xl px-4 py-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-slate-900">Admin Profile</h1>
                <p className="text-sm text-slate-600">View and update your profile details</p>
            </div>

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

            <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                    <h2 className="mb-4 text-lg font-semibold text-slate-700">Account</h2>

                    <div className="space-y-2 text-sm text-slate-700">
                        <div>
                            <span className="font-semibold">Username:</span>{" "}
                             {profile?.username ?? "--"}
                        </div>
                        <div>
                            <span className="font-semibold">Email:</span>{" "}
                             {profile?.email ?? "--"}
                        </div>
                        <div>
                            <span className="font-semibold">Role:</span>{" "}
                            Administrator
                        </div>
                    </div>
                </div>

                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                    <h2 className="mb-4 text-lg font-semibold text-slate-700">
                        Edit Profile
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <input
                                name="first_name"
                                value={formData.first_name}
                                onChange={handleChange}
                                placeholder="First Name"
                                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring focus:ring-green-500"
                            />
                            <input
                                name="last_name"
                                value={formData.last_name}
                                onChange={handleChange}
                                placeholder="Last Name"
                                className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring focus:ring-green-500"
                            />
                        </div>

                        <input
                            name="phone_number"
                            value={formData.phone_number}
                            onChange={handleChange}
                            placeholder="Phone Number (+254..."
                            className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring focus:ring-green-500"
                        />

                        <input
                            name="date_of_birth"
                            value={formData.date_of_birth}
                            onChange={handleChange}
                            placeholder="Date of Birth (YYYY-MM-DD)"
                            className="w-full rounded-xl border px-3 py-2 text-sm focus:ring-2 focus:ring focus:ring-green-500"
                        />

                        <button
                            type="submit"
                            className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
                            disabled={status === "loading"}
                        >
                            {status === "loading" ? "Saving..." : "Save Changes"}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
