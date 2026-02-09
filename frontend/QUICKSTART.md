# 🚀 Quick Start Guide - Pulse Pay Admin Dashboard

## Prerequisites
- Node.js 16+ installed
- Backend API running on port 5000
- Admin user account

## Installation

1. **Navigate to frontend directory**:
```bash
cd /home/sylvia-malala/phase_4/Pulse-pay/frontend
```

2. **Install dependencies** (if not already done):
```bash
npm install
```

3. **Configure environment**:
```bash
# Create .env file
cp .env.example .env

# Edit .env if needed
nano .env
```

4. **Start development server**:
```bash
npm run dev
```

5. **Open browser**:
```
http://localhost:5173
```

## Admin Dashboard Access

### Route Structure
```
/admin/dashboard     - Main overview page
/admin/users         - User management
/admin/wallets       - Wallet management
/admin/transactions  - Transaction monitoring
/admin/kyc           - KYC verification
/admin/analytics     - Analytics & reports
```

### First Time Setup

1. **Login as admin**:
   - Go to `http://localhost:5173/login`
   - Enter admin credentials
   - Ensure user has `role: 'admin'`

2. **Access dashboard**:
   - Navigate to `/admin/dashboard`
   - Or click admin link in navigation

3. **Explore features**:
   - Use sidebar to navigate sections
   - Try filtering and searching
   - View analytics and charts

## Features Overview

### 📊 Dashboard
- **What**: System overview with key metrics
- **Access**: `/admin/dashboard`
- **Actions**: View stats, refresh data

### 👥 Users
- **What**: Manage all users
- **Access**: `/admin/users`
- **Actions**: 
  - Search users
  - Filter by status/KYC
  - Activate/deactivate accounts

### 💰 Wallets
- **What**: Monitor all wallets
- **Access**: `/admin/wallets`
- **Actions**:
  - View balances
  - Filter by status
  - Search by user

### 💸 Transactions
- **What**: Transaction monitoring
- **Access**: `/admin/transactions`
- **Actions**:
  - Filter by date/amount/status
  - Reverse transactions (with OTP)
  - View transaction details

### ✅ KYC Verification
- **What**: Verify user identities
- **Access**: `/admin/kyc`
- **Actions**:
  - Review documents
  - Approve/reject verifications
  - Provide rejection reasons

### 📈 Analytics
- **What**: Business insights
- **Access**: `/admin/analytics`
- **Actions**:
  - View revenue trends
  - Analyze transaction patterns
  - See top performers

## Common Tasks

### Task 1: Find and Deactivate a User
```
1. Go to /admin/users
2. Enter email/username in search
3. Click "Apply Filters"
4. Click "Deactivate" button
5. Confirm action
```

### Task 2: Approve KYC
```
1. Go to /admin/kyc
2. Review submitted documents
3. Click "Approve" button
4. User is verified
```

### Task 3: Reverse Transaction
```
1. Go to /admin/transactions
2. Find completed transaction
3. Click "Reverse" button
4. Enter OTP code
5. Confirm reversal
```

### Task 4: View Analytics
```
1. Go to /admin/analytics
2. Select time period (7/30/60/90 days)
3. View charts and insights
4. Check top users
```

## Keyboard Shortcuts

- `Ctrl/Cmd + K` - Quick search (if implemented)
- `Esc` - Close modals
- `Tab` - Navigate forms
- `Enter` - Submit forms

## Troubleshooting

### Issue: Can't access admin dashboard
**Solution**: 
- Check if logged in
- Verify user has admin role
- Check token in localStorage

### Issue: Data not loading
**Solution**:
- Check backend is running (port 5000)
- Verify API_BASE_URL in .env
- Check browser console for errors
- Try refreshing the page

### Issue: Charts not showing
**Solution**:
- Ensure date range has data
- Check console for errors
- Try different time period

### Issue: Can't reverse transaction
**Solution**:
- Verify transaction is completed
- Check OTP code is correct
- Ensure you have admin permissions

## Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Run tests (if configured)
npm run test
```

## File Locations

### Configuration
- Environment: `frontend/.env`
- Vite config: `frontend/vite.config.js`
- Tailwind: `frontend/tailwind.config.js`

### Source Code
- Components: `frontend/src/components/admin/`
- Pages: `frontend/src/pages/admin/`
- Redux Store: `frontend/src/store/`
- API Services: `frontend/src/services/`

### Documentation
- Admin README: `frontend/ADMIN_README.md`
- Implementation: `frontend/IMPLEMENTATION_SUMMARY.md`
- This guide: `frontend/QUICKSTART.md`

## API Endpoints Used

```
GET    /api/admin/users
PUT    /api/admin/users/:id/status
GET    /api/admin/wallets
GET    /api/admin/transactions
POST   /api/admin/transactions/:id/reverse
GET    /api/admin/stats
GET    /api/admin/kyc/pending
POST   /api/admin/kyc/:id/verify
GET    /api/admin/analytics/profit-trends
GET    /api/admin/suspicious-activities
```

## Best Practices

1. **Security**
   - Always log out when done
   - Don't share admin credentials
   - Verify actions before confirming

2. **Data Management**
   - Use filters to find data quickly
   - Refresh data regularly
   - Check multiple sources before decisions

3. **KYC Verification**
   - Review documents carefully
   - Provide clear rejection reasons
   - Double-check identity details

4. **Transaction Reversal**
   - Only reverse when necessary
   - Keep record of reversal reason
   - Verify with user first

## Support

- Check console logs for errors
- Review network tab in DevTools
- Check backend logs
- Refer to ADMIN_README.md for details

## Next Steps

1. Customize dashboard widgets
2. Add more filters
3. Export data features
4. Create reports
5. Add notifications
6. Implement real-time updates

---

**Need Help?** Check ADMIN_README.md or contact the development team.
