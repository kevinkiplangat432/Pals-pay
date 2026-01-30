import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";

const Login = () => <div className="p-10">Login Page</div>;
const Signup = () => <div className="p-10">Signup Page</div>;
const FAQs = () => <div className="p-10">FAQs Page</div>;

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/faqs" element={<FAQs />} />
      </Routes>
    </Router>
  );
}
