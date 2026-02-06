import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

// Admin Components
import AdminLayout from "./components/admin/AdminLayout";
import AdminProtectedRoute from "./components/admin/AdminProtectedRoute";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminWallets from "./pages/admin/AdminWallets";
import AdminTransactions from "./pages/admin/AdminTransactions";
import AdminKyc from "./pages/admin/AdminKyc";
import AdminAnalytics from "./pages/admin/AdminAnalytics";

const FAQs = () => <div className="p-10">FAQs Page</div>;

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/faqs" element={<FAQs />} />
        
        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <AdminProtectedRoute>
              <AdminLayout />
            </AdminProtectedRoute>
          }
        >
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="wallets" element={<AdminWallets />} />
          <Route path="transactions" element={<AdminTransactions />} />
          <Route path="kyc" element={<AdminKyc />} />
          <Route path="analytics" element={<AdminAnalytics />} />
        </Route>
      </Routes>
    </Router>
  );
}
