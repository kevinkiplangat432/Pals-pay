import { NavLink } from 'react-router-dom';

const UserSidebar = ({ isOpen }) => {
  const navLinks = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard' },
    { path: '/wallet', icon: '💰', label: 'Wallet' },
    { path: '/transactions', icon: '💸', label: 'Transactions' },
    { path: '/payment-methods', icon: '💳', label: 'Payment Methods' },
    { path: '/profile', icon: '👤', label: 'Profile' },
    { path: '/kyc', icon: '✅', label: 'KYC Verification' },
  ];

  return (
    <aside
      className={`${
        isOpen ? 'w-64' : 'w-20'
      } bg-gradient-to-b from-green-600 to-green-800 text-white transition-all duration-300 ease-in-out flex flex-col`}
    >
      <div className="p-6 flex items-center justify-center border-b border-green-500">
        <h1 className={`font-bold text-xl ${isOpen ? 'block' : 'hidden'}`}>
          Pal's Pay
        </h1>
        <span className={`text-2xl ${isOpen ? 'hidden' : 'block'}`}>PP</span>
      </div>

      <nav className="flex-1 py-6">
        <ul className="space-y-2 px-3">
          {navLinks.map((link) => (
            <li key={link.path}>
              <NavLink
                to={link.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 rounded-lg transition-colors duration-200 ${
                    isActive
                      ? 'bg-green-700 text-white shadow-md'
                      : 'text-green-100 hover:bg-green-700 hover:text-white'
                  }`
                }
              >
                <span className="text-2xl">{link.icon}</span>
                <span className={`ml-3 font-medium ${isOpen ? 'block' : 'hidden'}`}>
                  {link.label}
                </span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-green-500">
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'justify-center'}`}>
          <span className={`text-sm text-green-200 ${isOpen ? 'block' : 'hidden'}`}>
            v1.0.0
          </span>
        </div>
      </div>
    </aside>
  );
};

export default UserSidebar;
