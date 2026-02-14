import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import { login, verifyLoginOTP, clearAuthError } from "../features/authSlice";
import PageWithRepeatingLogo from "../components/common/PageWithRepeatingLogo";

export default function Login() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { user, status, error, otpRequired, otpUserId } = useSelector(
    (state) => state.auth
  );
  const [isOtpStage, setIsOtpStage] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    otp: "",
  });

  useEffect(() => {
    if (user && !user.requires_verification) {
      navigate(user.is_admin ? "/admin/dashboard" : "/dashboard", { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (otpRequired) {
      setIsOtpStage(true);
    }
  }, [otpRequired]);

  const handleChange = (e) => {
    dispatch(clearAuthError());
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    if (isOtpStage) {
      const result = await dispatch(
        verifyLoginOTP({
          user_id: otpUserId,
          otp_code: formData.otp,
        })
      );

      if (verifyLoginOTP.fulfilled.match(result)) {
        const userData = result.payload?.user;
        navigate(userData?.is_admin ? "/admin/dashboard" : "/dashboard", { replace: true });
      }
    } else {
      await dispatch(login({
        email: formData.email,
        password: formData.password,
      }));
    }
  };

  return (
    <PageWithRepeatingLogo>
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-white flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <h1 className="text-4xl font-bold">
            Pal's<span className="text-green-600">Pay</span>
          </h1>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {isOtpStage ? "Enter OTP Code" : "Sign in to your account"}
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{" "}
          <Link to="/signup" className="font-medium text-green-600 hover:text-green-500">
            create a new account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl rounded-2xl sm:px-10">
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleLogin}>
            {!isOtpStage ? (
              <>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email address
                  </label>
                  <div className="mt-1">
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={formData.email}
                      onChange={handleChange}
                      className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                      placeholder="Enter your email"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <div className="mt-1">
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="current-password"
                      required
                      value={formData.password}
                      onChange={handleChange}
                      className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                      placeholder="Enter your password"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    <Link to="/forgot-password" className="font-medium text-green-600 hover:text-green-500">
                      Forgot your password?
                    </Link>
                  </div>
                </div>
              </>
            ) : (
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                  OTP Code
                </label>
                <div className="mt-1">
                  <input
                    id="otp"
                    name="otp"
                    type="text"
                    required
                    value={formData.otp}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                    placeholder="Enter 6-digit OTP"
                    maxLength={6}
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  Check your email or phone for the OTP code
                </p>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={status === "loading"}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === "loading" ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Processing...
                  </span>
                ) : isOtpStage ? (
                  "Verify OTP"
                ) : (
                  "Sign in"
                )}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Secure login with bank-level encryption
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </PageWithRepeatingLogo>
  );
}