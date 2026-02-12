# PalsPay - Digital Wallet & Payment Platform

A full-stack digital wallet application supporting multi-currency transactions, M-Pesa integration, KYC verification, and comprehensive admin management.
### live links
#### frontend: https://pals-pay-du73.vercel.app/
#### backend : https://pals-pay.onrender.com
#### database: postgresql://pals_pay_db_user:e06tMRqzItWJ7Hjwwf5j5lNlpOZhiEue@dpg-d66m2i06fj8s7398ke10-a/pals_pay_db

##  Features

### User Features
- **Digital Wallet** - Multi-currency wallet with real-time balance tracking
- **M-Pesa Integration** - Deposit and withdraw via M-Pesa STK Push
- **Money Transfers** - Send money to other users instantly
- **Payment Methods** - Manage multiple payment methods
- **KYC Verification** - Document upload and verification system
- **Transaction History** - Complete transaction tracking and filtering
- **Profile Management** - Update personal information and settings

### Admin Features
- **User Management** - View, activate/deactivate users, filter by KYC status
- **KYC Verification** - Review and approve/reject KYC submissions
- **Transaction Monitoring** - View all transactions with advanced filtering
- **Wallet Management** - Monitor all user wallets and balances
- **Analytics Dashboard** - System statistics and insights
- **Audit Logs** - Complete activity tracking

## Tech Stack

### Frontend
- **React 18** with Vite
- **Redux Toolkit** for state management
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Axios** for API calls

### Backend
- **Flask** (Python) REST API
- **PostgreSQL** database
- **SQLAlchemy** ORM
- **Flask-JWT-Extended** for authentication
- **Flask-CORS** for cross-origin requests
- **Flask-Migrate** for database migrations

### Payment Integration
- **M-Pesa Daraja API** (Lipa Na M-Pesa, B2C)
- **Flutterwave** (configured, ready to integrate)

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- pipenv (Python package manager)
- npm or yarn

##  Installation

### 1. Clone Repository

```bash
git clone https://github.com/kevinkiplangat432/Pals-pay.git
cd Pals-pay
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pipenv install

# Create PostgreSQL database
createdb pals_db
createuser palsuser -P  # Password: palspassword

# Run migrations
pipenv run flask db upgrade

# Seed database (optional)
pipenv run python seed_users.py

# Start backend server
pipenv run python run.py
```

Backend runs on: http://localhost:5000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: http://localhost:5173

##  Configuration


### Frontend Configuration

Update `frontend/src/utils/api.js` if backend URL changes:
```javascript
const API_BASE_URL = 'http://localhost:5000';
```

##  Testing M-Pesa Integration

### Quick Setup

1. **Create Daraja Account**
   - Visit: https://developer.safaricom.co.ke/
   - Create sandbox app
   - Get credentials (Consumer Key, Secret, Passkey)

2. **Install ngrok**
   ```bash
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar -xvzf ngrok-v3-stable-linux-amd64.tgz
   sudo mv ngrok /usr/local/bin/
   ngrok config add-authtoken YOUR_TOKEN
   ```

3. **Start ngrok**
   ```bash
   ngrok http 5000
   ```

4. **Update .env with ngrok URL**
   ```env
   MPESA_CALLBACK_URL=https://abc123.ngrok.io/api/v1/mpesa/callback
   ```

5. **Test Deposit**
   ```bash
   curl -X POST http://localhost:5000/api/v1/deposit/mpesa \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"amount": 10, "phone_number": "254708374149"}'
   ```

**Sandbox Credentials:**
- Phone: 254708374149
- PIN: 174379

See `MPESA_QUICKSTART.md` for detailed guide.

## User Accounts

### Create Admin Account

```bash
cd backend
pipenv run python make_admin.py
# Enter your email when prompted
```

### Test Users (from seed_users.py)

```
Email: john.doe@example.com
Password: Password123!
```

10 test users available with verified KYC and 10,000 KES balance.

## Project Structure

```
Pals-pay/
├── backend/
│   ├── app/
│   │   ├── auth/              # Authentication & decorators
│   │   ├── models/            # Database models
│   │   ├── Routes/            # API endpoints
│   │   ├── services/          # Business logic (M-Pesa, KYC, etc.)
│   │   └── __init__.py        # App factory
│   ├── migrations/            # Database migrations
│   ├── .env                   # Environment variables
│   ├── config.py              # Configuration
│   └── run.py                 # Entry point
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── admin/         # Admin components
│   │   │   ├── user/          # User components
│   │   │   └── common/        # Shared components
│   │   ├── features/          # Redux slices
│   │   ├── pages/             # Page components
│   │   ├── store/             # Redux store
│   │   └── utils/             # Utilities
│   └── package.json
├── MPESA_QUICKSTART.md        # M-Pesa setup guide
├── MPESA_TESTING_GUIDE.md     # Detailed M-Pesa testing
└── README.md                  # This file
```

##  Security Features

- JWT-based authentication
- OTP verification for login
- Password hashing with bcrypt
- Role-based access control (Admin/User)
- KYC verification system
- Transaction audit logs
- CORS protection

##  Database Schema

### Main Tables
- **users** - User accounts and profiles
- **wallets** - User wallet balances
- **transactions** - All financial transactions
- **kyc_verifications** - KYC documents and status
- **payment_methods** - User payment methods
- **audit_logs** - System activity logs

##  Deployment

### Backend (Production)

1. Update environment variables for production
2. Set `FLASK_ENV=production`
3. Use production database
4. Configure production M-Pesa credentials
5. Use real domain for callbacks (not ngrok)

### Frontend (Production)

1. Update API base URL
2. Build production bundle:
   ```bash
   npm run build
   ```
3. Deploy `dist/` folder to hosting service

##  Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify database credentials in .env
- Run migrations: `pipenv run flask db upgrade`

### M-Pesa callbacks not received
- Ensure ngrok is running
- Check callback URL in .env matches ngrok URL
- Restart backend after updating .env
- Check ngrok dashboard: http://localhost:4040

### Frontend can't connect to backend
- Verify backend is running on port 5000
- Check CORS configuration in backend
- Verify API_BASE_URL in frontend

##  Scripts

### Backend
```bash
pipenv run python run.py              # Start server
pipenv run python seed_users.py       # Seed test users
pipenv run python make_admin.py       # Make user admin
pipenv run flask db migrate           # Create migration
pipenv run flask db upgrade           # Run migrations
```

### Frontend
```bash
npm run dev                           # Start dev server
npm run build                         # Build for production
npm run preview                       # Preview production build
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Authors

- Kevin Kiplangat - Initial work
- Sylvia Malala
- wise mutuku
- Meri alea

## Acknowledgments

- Safaricom Daraja API for M-Pesa integration
- Flask and React communities
- All contributors

## Support
for any issues contact kiplangatkevin335@gmail.com

**Built with ❤️ for seamless digital payments**
