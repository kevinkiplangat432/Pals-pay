import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, Link } from "react-router-dom";
import { useGoogleLogin } from '@react-oauth/google';
import { register, clearAuthError } from "../features/authSlice";
import PageWithRepeatingLogo from "../components/common/PageWithRepeatingLogo";

export default function Signup() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { user, status, error } = useSelector((state) => state.auth);
  const [countries, setCountries] = useState([]);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    phone_number: "",
    country_code: "KE",
    account_type: "individual",
    notify_email: true,
    notify_sms: true,
    accept_terms: false,
  });

  useEffect(() => {
    if (user) {
      navigate("/verify-email");
    }

    // Fetch supported countries
    fetchCountries();
  }, [user, navigate]);

  const fetchCountries = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/v1/auth/countries");
      const data = await response.json();
      setCountries(data.countries || []);
    } catch (error) {
      console.error("Failed to fetch countries:", error);
    }
  };

  const handleChange = (e) => {
    dispatch(clearAuthError());
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Frontend validation
    if (!formData.name.trim()) {
      alert("Please enter your name");
      return;
    }

    if (!formData.email.trim()) {
      alert("Please enter your email");
      return;
    }

    if (!formData.accept_terms) {
      alert("Please accept the Terms and Conditions");
      return;
    }

    // Dispatch register thunk
    const result = await dispatch(register(formData));

    if (register.fulfilled.match(result)) {
      if (result.payload.requires_verification) {
        navigate("/verify-email");
      } else {
        navigate("/wallet");
      }
    }
  };

  const handleGoogleSignIn = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async (tokenResponse) => {
      try {
        // Get user info from Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        const userInfo = await userInfoResponse.json();

        // Send to backend
        const response = await fetch('http://localhost:5000/api/v1/auth/google', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token: tokenResponse.access_token,
            email: userInfo.email,
            name: userInfo.name,
            picture: userInfo.picture,
          }),
        });

        const data = await response.json();

        if (response.ok) {
          // Store token and redirect
          localStorage.setItem('access_token', data.access_token);
          navigate('/wallet');
        } else {
          alert(data.message || 'Google sign-in failed');
        }
      } catch (error) {
        console.error('Google sign-in error:', error);
        alert('Failed to sign in with Google');
      }
    },
    onError: () => {
      alert('Google sign-in failed. Please try again.');
    },
  });


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
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-green-600 hover:text-green-500">
            Sign in
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

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  placeholder="John Doe"
                />
              </div>
            </div>

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
                  placeholder="you@example.com"
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
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  placeholder="At least 8 characters"
                  minLength={8}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Password must be at least 8 characters long
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="country_code" className="block text-sm font-medium text-gray-700">
                  Country
                </label>
                <div className="mt-1">
                  <select
                    id="country_code"
                    name="country_code"
                    required
                    value={formData.country_code}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                  >
                    {countries.map((country) => (
                      <option key={country.code} value={country.code}>
                        {country.flag} {country.name} ({country.dialing_code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700">
                  Phone Number
                </label>
                <div className="mt-1">
                  <input
                    id="phone_number"
                    name="phone_number"
                    type="tel"
                    required
                    value={formData.phone_number}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                    placeholder="712345678"
                  />
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="account_type" className="block text-sm font-medium text-gray-700">
                Account Type
              </label>
              <div className="mt-1">
                <select
                  id="account_type"
                  name="account_type"
                  required
                  value={formData.account_type}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500"
                >
                  <option value="individual">Individual</option>
                  <option value="business">Business</option>
                  <option value="trust">Trust</option>
                </select>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700">
                Notification Preferences
              </label>
              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    id="notify_email"
                    name="notify_email"
                    type="checkbox"
                    checked={formData.notify_email}
                    onChange={handleChange}
                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                  />
                  <label htmlFor="notify_email" className="ml-2 block text-sm text-gray-700">
                    Email notifications
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    id="notify_sms"
                    name="notify_sms"
                    type="checkbox"
                    checked={formData.notify_sms}
                    onChange={handleChange}
                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                  />
                  <label htmlFor="notify_sms" className="ml-2 block text-sm text-gray-700">
                    SMS notifications
                  </label>
                </div>
              </div>
            </div>

            {/* Terms and Conditions */}
            <div className="flex items-start">
              <input
                id="accept_terms"
                name="accept_terms"
                type="checkbox"
                checked={formData.accept_terms}
                onChange={handleChange}
                className="h-4 w-4 mt-1 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                required
              />
              <label htmlFor="accept_terms" className="ml-2 block text-sm text-gray-700">
                I agree to the{" "}
                <button
                  type="button"
                  onClick={() => setShowTermsModal(true)}
                  className="text-green-600 hover:text-green-700 font-medium underline"
                >
                  Terms and Conditions
                </button>
              </label>
            </div>

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
                    Creating Account...
                  </span>
                ) : (
                  "Create Account"
                )}
              </button>
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>

            {/* Google Sign In */}
            <div>
              <button
                type="button"
                onClick={handleGoogleSignIn}
                className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-xl shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign up with Google
              </button>
            </div>

            <p className="text-xs text-gray-500 text-center">
              By creating an account, you agree to our Terms of Service and Privacy Policy.
            </p>
          </form>
        </div>
      </div>

      {/* Terms and Conditions Modal */}
      {showTermsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-gray-900">Terms and Conditions</h3>
                <button
                  onClick={() => setShowTermsModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
              <div className="prose prose-sm max-w-none">
                <h4 className="text-lg font-semibold text-gray-900 mb-3">1. Acceptance of Terms</h4>
                <p className="text-gray-600 mb-4">
                  By creating an account with PalsPay, you agree to be bound by these Terms and Conditions. If you do not agree to these terms, please do not use our services.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">2. Account Registration</h4>
                <p className="text-gray-600 mb-4">
                  You must provide accurate, current, and complete information during registration. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">3. KYC Verification</h4>
                <p className="text-gray-600 mb-4">
                  To comply with regulatory requirements, you must complete Know Your Customer (KYC) verification. This includes providing valid identification documents. Failure to complete KYC may result in limited account functionality.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">4. Wallet Services</h4>
                <p className="text-gray-600 mb-4">
                  PalsPay provides digital wallet services for storing, sending, and receiving money. We support multiple currencies and payment methods including M-Pesa. Transaction fees may apply.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">5. Transaction Limits</h4>
                <p className="text-gray-600 mb-4">
                  Daily and monthly transaction limits apply based on your account type and verification level. These limits are subject to change and will be communicated to you.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">6. Fees and Charges</h4>
                <p className="text-gray-600 mb-4">
                  We charge fees for certain transactions including transfers, withdrawals, and currency conversions. All fees are clearly displayed before you confirm a transaction.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">7. Security</h4>
                <p className="text-gray-600 mb-4">
                  You must keep your account credentials secure. Enable two-factor authentication when available. Report any unauthorized access immediately.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">8. Prohibited Activities</h4>
                <p className="text-gray-600 mb-4">
                  You may not use PalsPay for illegal activities, money laundering, fraud, or any activity that violates applicable laws. We reserve the right to suspend or terminate accounts involved in prohibited activities.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">9. Liability</h4>
                <p className="text-gray-600 mb-4">
                  PalsPay is not liable for losses resulting from unauthorized access to your account, service interruptions, or third-party payment provider issues. We maintain insurance and security measures to protect your funds.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">10. Privacy</h4>
                <p className="text-gray-600 mb-4">
                  We collect and process your personal data in accordance with our Privacy Policy. Your data is encrypted and stored securely.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">11. Termination</h4>
                <p className="text-gray-600 mb-4">
                  You may close your account at any time. We may suspend or terminate your account if you violate these terms or engage in suspicious activity.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">12. Changes to Terms</h4>
                <p className="text-gray-600 mb-4">
                  We may update these Terms and Conditions from time to time. Continued use of our services after changes constitutes acceptance of the new terms.
                </p>

                <h4 className="text-lg font-semibold text-gray-900 mb-3">13. Contact</h4>
                <p className="text-gray-600 mb-4">
                  For questions about these terms, contact us at support@palspay.com
                </p>

                <p className="text-sm text-gray-500 mt-6">
                  Last updated: February 2026
                </p>
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setShowTermsModal(false)}
                className="w-full py-3 px-4 bg-green-600 hover:bg-green-700 text-white font-medium rounded-xl transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </PageWithRepeatingLogo>
  );
}