import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Faq from "./pages/Faqs";


// User Pages
import WalletPage from "./pages/WalletPage";
import UserProfilePage from "./pages/UserProfilePage";
import KycPage from "./pages/KycPage";
import PaymentMethodsPage from "./pages/PaymentMethods";
import TransactionsPage from "./pages/TransactionsPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";

// Admin Components
import AdminLayout from "./components/admin/AdminLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminWallets from "./pages/admin/AdminWallets";
import AdminTransactions from "./pages/admin/AdminTransactions";
import AdminKyc from "./pages/admin/AdminKyc";
import AdminAnalytics from "./pages/admin/AdminAnalytics";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/Faqs" element={<Faq />} />

      {/* User Protected Routes */}
      <Route
        path="/wallet"
        element={
          <ProtectedRoute>
            <WalletPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <UserProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/kyc"
        element={
          <ProtectedRoute>
            <KycPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/payment-methods"
        element={
          <ProtectedRoute>
            <PaymentMethodsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/transactions"
        element={
          <ProtectedRoute>
            <TransactionsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />

      {/* Admin Protected Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireAdmin>
            <AdminLayout />
          </ProtectedRoute>
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
  );
}

export default App;