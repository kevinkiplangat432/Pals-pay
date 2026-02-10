import { Navigate } from "react-router-dom";
import { useSelector } from "react-redux";

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, status } = useSelector((state) => state.auth);
  const token = localStorage.getItem("access_token");

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && user?.is_admin !== true) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;