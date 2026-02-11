import { NavLink } from 'react-router-dom';

const AdminSidebar = ({ isOpen }) => {
  const navLinks = [
    { path: '/admin/dashboard', icon: 'chart', label: 'Dashboard' },
    { path: '/admin/users', icon: 'users', label: 'Users' },
    { path: '/admin/wallets', icon: 'wallet', label: 'Wallets' },
    { path: '/admin/transactions', icon: 'dollar', label: 'Transactions' },
    { path: '/admin/kyc', icon: 'check', label: 'KYC Verification' },
    { path: '/admin/analytics', icon: 'analytics', label: 'Analytics' },
  ];

  const getIcon = (iconName) => {
    const icons = {
      chart: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      users: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ),
      wallet: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      dollar: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
      check: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      analytics: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    };
    return icons[iconName] || icons.chart;
  };

  return (
    <aside
      className={`${
        isOpen ? 'w-64' : 'w-20'
      } bg-gradient-to-b from-green-600 to-green-800 text-white transition-all duration-300 ease-in-out flex flex-col`}
    >
      <div className="p-6 flex items-center justify-center border-b border-green-500">
        <h1 className={`font-bold text-xl ${isOpen ? 'block' : 'hidden'}`}>
          Pulse Pay Admin
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
                <span className="flex items-center justify-center w-8 h-8">{getIcon(link.icon)}</span>
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

export default AdminSidebar;
