import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          Pal’s<span className="text-green-600">Pay</span>
        </h1>

        <nav className="space-x-6">
          <Link to="/" className="text-gray-700">Home</Link>
          <Link to="/login" className="text-gray-700">Login</Link>
          <Link
            to="/signup"
            className="bg-green-600 text-white px-4 py-2 rounded-md"
          >
            Sign Up
          </Link>
          <Link to="/faqs" className="text-gray-700">FAQs</Link>
        </nav>
      </div>
    </header>
  );
}
