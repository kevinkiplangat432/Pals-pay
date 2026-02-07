# Pulse Pay Admin Dashboard

A comprehensive admin dashboard built with React, Redux Toolkit, and Tailwind CSS for managing the Pulse Pay wallet application.

## Features

### 📊 Dashboard Overview
- Real-time system statistics
- User metrics (total, active, new today, KYC verified)
- Wallet statistics (total balance, average balance)
- Transaction metrics (today's volume, fees, last 30 days)
- KYC status overview
- Revenue insights

### 👥 User Management
- View all users with pagination
- Search users by email, username, or phone
- Filter by status (active/inactive) and KYC status
- Toggle user status (activate/deactivate)
- View user details including wallet and KYC information

### 💰 Wallet Management
- View all wallets with user details
- Search by user information
- Filter by wallet status and minimum balance
- View wallet balances and currencies
- Track wallet creation dates

### 💸 Transaction Management
- View all transactions with advanced filtering
- Filter by status, type, date range, and amount
- View transaction details with sender/receiver information
- Reverse completed transactions (requires OTP)
- Real-time transaction monitoring

### ✅ KYC Verification
- View pending KYC verifications
- Review submitted documents (front and back)
- Approve or reject verifications
- Provide rejection reasons
- Track verification status

### 📈 Analytics & Insights
- Daily revenue trends with interactive charts
- Transaction volume analysis
- Revenue by transaction type distribution
- Top revenue-generating users
- Customizable time periods (7, 30, 60, 90 days)
- Period summary statistics

## Tech Stack

- **Frontend Framework**: React 19.2.4
- **State Management**: Redux Toolkit 2.11.2
- **Routing**: React Router DOM 7.13.0
- **HTTP Client**: Axios 1.13.4
- **Charts**: Recharts 3.7.0
- **Styling**: Tailwind CSS 3.4.19
- **Date Formatting**: date-fns 4.1.0
- **Build Tool**: Vite (Rolldown)

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set your API base URL:
```
VITE_API_BASE_URL=http://localhost:5000/api
```

3. Start the development server:
```bash
npm run dev
```

## Project Structure

```
frontend/src/
├── components/
│   └── admin/
│       ├── AdminLayout.jsx       # Main admin layout
│       ├── AdminSidebar.jsx      # Navigation sidebar
│       ├── AdminHeader.jsx       # Top header bar
│       ├── AdminProtectedRoute.jsx # Route protection
│       └── StatsCard.jsx         # Reusable stat card
├── pages/
│   └── admin/
│       ├── AdminDashboard.jsx    # Dashboard overview
│       ├── AdminUsers.jsx        # User management
│       ├── AdminWallets.jsx      # Wallet management
│       ├── AdminTransactions.jsx # Transaction management
│       ├── AdminKyc.jsx          # KYC verification
│       └── AdminAnalytics.jsx    # Analytics & insights
├── store/
│   ├── store.js                  # Redux store configuration
│   └── slices/
│       ├── adminUsersSlice.js    # User state management
│       ├── adminWalletsSlice.js  # Wallet state management
│       ├── adminTransactionsSlice.js # Transaction state
│       ├── adminAnalyticsSlice.js    # Analytics state
│       └── adminKycSlice.js      # KYC state management
├── services/
│   ├── api.js                    # Axios instance
│   └── adminApi.js               # Admin API endpoints
└── App.jsx                       # Main app with routing
```

## Admin Routes

- `/admin/dashboard` - System overview and statistics
- `/admin/users` - User management interface
- `/admin/wallets` - Wallet management interface
- `/admin/transactions` - Transaction monitoring
- `/admin/kyc` - KYC verification queue
- `/admin/analytics` - Analytics and reporting

## API Integration

The admin dashboard connects to the following backend endpoints:

- `GET /api/admin/users` - Fetch all users
- `PUT /api/admin/users/:id/status` - Toggle user status
- `GET /api/admin/wallets` - Fetch all wallets
- `GET /api/admin/transactions` - Fetch all transactions
- `POST /api/admin/transactions/:id/reverse` - Reverse transaction
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/kyc/pending` - Get pending KYC verifications
- `POST /api/admin/kyc/:id/verify` - Verify KYC
- `GET /api/admin/analytics/profit-trends` - Get profit trends

## State Management

Redux Toolkit is used for state management with the following slices:

- **adminUsers**: Manages user data, filters, and pagination
- **adminWallets**: Handles wallet data and filtering
- **adminTransactions**: Controls transaction data and operations
- **adminAnalytics**: Manages analytics data and trends
- **adminKyc**: Handles KYC verification queue

## Features & Functionality

### Real-time Data Updates
- Automatic data refresh on page load
- Manual refresh buttons for instant updates
- Error handling with user-friendly messages

### Advanced Filtering
- Multi-criteria filtering across all sections
- Search functionality with fuzzy matching
- Date range filtering for transactions
- Amount range filtering

### Responsive Design
- Mobile-friendly interface
- Collapsible sidebar for smaller screens
- Responsive charts and tables
- Touch-friendly controls

### Security
- Protected routes with authentication check
- Role-based access control (admin only)
- OTP verification for sensitive operations
- Automatic token refresh and logout

## Usage

### Accessing the Dashboard

1. Log in with admin credentials at `/login`
2. Navigate to `/admin/dashboard` or click the admin link
3. Use the sidebar to navigate between sections

### Managing Users

1. Go to "Users" section
2. Use filters to find specific users
3. Click "Activate" or "Deactivate" to toggle user status
4. View user details including wallet and KYC info

### Verifying KYC

1. Navigate to "KYC Verification"
2. Review submitted documents
3. Click "Approve" to verify or "Reject" to deny
4. Provide rejection reason if denying

### Reversing Transactions

1. Go to "Transactions" section
2. Find the completed transaction to reverse
3. Click "Reverse" button
4. Enter OTP code when prompted

### Viewing Analytics

1. Visit "Analytics" page
2. Select time period (7, 30, 60, or 90 days)
3. View charts and top performers
4. Export data if needed

## Development

### Running Tests
```bash
npm run test
```

### Building for Production
```bash
npm run build
```

### Linting
```bash
npm run lint
```

## Contributing

When adding new features:

1. Create new Redux slice if needed
2. Add API endpoints to `adminApi.js`
3. Create page component in `pages/admin/`
4. Add route in `App.jsx`
5. Update sidebar navigation in `AdminSidebar.jsx`

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lazy loading for routes
- Optimized Redux selectors
- Efficient re-rendering with React.memo
- Debounced search inputs
- Paginated data loading

## Notes

- All monetary values are displayed in USD
- Dates are formatted using `date-fns` in local timezone
- Charts use Recharts library for responsive visualizations
- State management follows Redux best practices
- Clean, human-readable code with proper comments

## License

MIT
