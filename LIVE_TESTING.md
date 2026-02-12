# Live Wallet Testing - Production

## 🌐 Live URLs
- **Frontend:** https://pals-pay-du73.vercel.app/
- **Backend:** https://pals-pay.onrender.com
- **Database:** PostgreSQL (Render)

---

## ✅ Quick Test Checklist

### 1️⃣ Login & Access Wallet (2 min)
- [ ] Go to https://pals-pay-du73.vercel.app/
- [ ] Login with: kiplangatkevin335@gmail.com / bd2876qwac
- [ ] Navigate to "Wallet" page
- [ ] Verify balance displays

---

### 2️⃣ Check Wallet Stats (1 min)
- [ ] **Current Balance** - Shows amount in KES
- [ ] **Wallet Analytics** - Shows deposits/withdrawals/transfers
- [ ] **Transaction Summary** - Shows completed/pending/failed counts
- [ ] Click "Refresh" button - Stats reload

---

### 3️⃣ Test Transfer (3 min)
**Setup:** Need 2 users with phone numbers

**Steps:**
1. [ ] Get another user's phone from database
2. [ ] Fill transfer form:
   - Receiver phone: `254XXXXXXXXX`
   - Amount: `50`
   - Description: `Test`
3. [ ] Click "Send Transfer"
4. [ ] Check for success message
5. [ ] Verify balance decreased
6. [ ] Check analytics updated

**Quick DB Check:**
```sql
-- Get test user phones
SELECT email, phone_number FROM users LIMIT 5;
```

---

### 4️⃣ Test M-Pesa Deposit (5 min)
**Note:** Only works with sandbox phone or your real M-Pesa number

**Steps:**
1. [ ] Fill deposit form:
   - Amount: `10`
   - Phone: `254708374149` (sandbox) OR your real number
2. [ ] Click "Deposit"
3. [ ] Check phone for STK push
4. [ ] Enter PIN: `174379` (sandbox) OR your real PIN
5. [ ] Wait for callback (~30 seconds)
6. [ ] Verify balance increased
7. [ ] Check analytics updated

**Important:** 
- Sandbox deposits auto-reverse in 24 hours
- Real deposits use actual money!

---

### 5️⃣ Test Validations (2 min)

**Invalid Phone:**
- [ ] Transfer to: `254999999999`
- [ ] Should show: "User with this phone number not found"

**Self Transfer:**
- [ ] Transfer to: Your own phone
- [ ] Should show: "Cannot transfer to yourself"

**Insufficient Balance:**
- [ ] Transfer amount: `999999999`
- [ ] Should show: Balance error

---

### 6️⃣ Check Transaction History (1 min)
- [ ] Go to "Transactions" page
- [ ] Verify recent transactions appear
- [ ] Check transaction details are correct

---

## 🔍 Quick Database Checks

### Check Your Wallet
```sql
SELECT w.balance, w.available_balance, u.email 
FROM wallets w 
JOIN users u ON w.user_id = u.id 
WHERE u.email = 'kiplangatkevin335@gmail.com';
```

### Check Recent Transactions
```sql
SELECT 
  transaction_type,
  amount,
  status,
  created_at
FROM transactions
ORDER BY created_at DESC
LIMIT 5;
```

### Get Test User Phones
```sql
SELECT id, email, phone_number 
FROM users 
WHERE phone_number IS NOT NULL
LIMIT 5;
```

---

## 🐛 Common Issues

### Balance Not Showing
- Check browser console for errors
- Verify JWT token is valid
- Try logout/login

### Transfer Fails
- Ensure receiver phone exists in DB
- Check phone format: `254XXXXXXXXX`
- Verify sufficient balance

### M-Pesa Not Working
- Check backend logs on Render
- Verify callback URL in production .env
- Ensure M-Pesa credentials are correct

### Stats Show Zero
- Make at least 1 transaction first
- Click "Refresh" button
- Check transactions are "completed" status

---

## 📊 Expected Results

After successful testing:
- ✅ Balance updates in real-time
- ✅ Analytics show accurate numbers
- ✅ Transfers work between users
- ✅ M-Pesa deposits work (if configured)
- ✅ Validations prevent bad inputs
- ✅ Transaction history is accurate

---

## 🚀 Next Steps

1. **Create 2nd test user** for transfer testing
2. **Test with real M-Pesa** (small amount)
3. **Check mobile responsiveness**
4. **Test error scenarios**
5. **Verify all stats calculate correctly**

---

## 📞 Need Help?

**Backend Logs:** Check Render dashboard
**Frontend Errors:** Check browser console (F12)
**Database:** Use provided connection string

**Contact:** kiplangatkevin335@gmail.com
