# Wallet Testing Guide

## Prerequisites
- Backend running on https://pals-pay.onrender.com
- Frontend running on https://pals-pay-du73.vercel.app
- Two test user accounts with phone numbers
- M-Pesa sandbox credentials configured

## Test Accounts Setup

### User 1 (Sender)
- Email: john.doe@example.com
- Password: Password123!
- Phone: (check database)

### User 2 (Receiver)
- Email: jane.smith@example.com
- Password: Password123!
- Phone: (check database)

## Test Scenarios

### 1. Test Wallet Balance Display
**Steps:**
1. Login to frontend
2. Navigate to `/wallet`
3. Check "Current Balance" card displays

**Expected:**
- Balance shows in KES
- No errors in console

---

### 2. Test Wallet Analytics
**Steps:**
1. On wallet page, check "Wallet Analytics" section
2. Click "Refresh" button

**Expected:**
- Total Deposits: Shows sum of deposits (last 30 days)
- Total Withdrawals: Shows sum of withdrawals
- Total Transfers: Shows sum of transfers sent
- Transaction Count: Shows total transactions

---

### 3. Test Transaction Summary
**Steps:**
1. On wallet page, check "Transaction Summary" section
2. Change days input (e.g., 7, 30, 90)
3. Click "Load" button

**Expected:**
- Completed: Count of completed transactions
- Pending: Count of pending transactions
- Failed: Count of failed transactions
- Total Amount: Sum of all amounts

---

### 4. Test M-Pesa Deposit (Sandbox)
**Steps:**
1. Fill deposit form:
   - Amount: 10
   - Phone: 254708374149
2. Click "Deposit"
3. Enter PIN: 174379 on phone prompt

**Expected:**
- Success message appears
- Balance updates after callback
- Analytics updates
- Transaction appears in summary

**Note:** Sandbox auto-reverses after 24 hours

---

### 5. Test Transfer to Phone Number
**Steps:**
1. Get User 2's phone number from database
2. Fill transfer form:
   - Receiver phone: User 2's phone
   - Amount: 100
   - Description: "Test transfer"
3. Click "Send Transfer"

**Expected:**
- Success message
- User 1 balance decreases (amount + fee)
- User 2 balance increases (amount)
- Both analytics update
- Transaction shows in both user histories

---

### 6. Test Transfer Validations
**Test 6a: Invalid Phone**
- Receiver phone: 254999999999 (non-existent)
- Expected: "User with this phone number not found"

**Test 6b: Self Transfer**
- Receiver phone: Your own phone
- Expected: "Cannot transfer to yourself"

**Test 6c: Insufficient Balance**
- Amount: 999999999
- Expected: "Insufficient balance" or similar

**Test 6d: Invalid Amount**
- Amount: -50 or 0
- Expected: Validation error

---

### 7. Test Withdrawal (Basic)
**Steps:**
1. Create payment method first (if needed)
2. Fill withdraw form:
   - Amount: 50
   - Payment Method ID: (your payment method ID)
3. Click "Withdraw"

**Expected:**
- Success message
- Balance decreases
- Transaction recorded
- Analytics updates

**Note:** Currently just database transaction, no actual M-Pesa B2C

---

### 8. Test Real-time Updates
**Steps:**
1. Open wallet page
2. Make a deposit or transfer
3. Check if stats update automatically

**Expected:**
- Balance updates
- Analytics refresh
- Transaction summary updates

---

### 9. Test Error Handling
**Test 9a: Network Error**
- Disconnect internet
- Try any operation
- Expected: Error message displayed

**Test 9b: Invalid Token**
- Clear localStorage
- Refresh page
- Expected: Redirect to login

---

### 10. Test Multiple Transactions
**Steps:**
1. Make 3 deposits of 10 KES each
2. Make 2 transfers of 50 KES each
3. Check analytics

**Expected:**
- Total Deposits: 30 KES
- Total Transfers: 100 KES
- Transaction Count: 5
- All transactions in summary

---

## API Testing (Using curl or Postman)

### Get Wallet Summary
```bash
curl -X GET https://pals-pay.onrender.com/api/v1/wallet/summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Analytics
```bash
curl -X GET https://pals-pay.onrender.com/api/v1/wallet/analytics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Transaction Summary
```bash
curl -X GET "https://pals-pay.onrender.com/api/v1/wallet/transactions/summary?days=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Deposit via M-Pesa
```bash
curl -X POST https://pals-pay.onrender.com/api/v1/wallet/deposit/mpesa \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10,
    "phone_number": "254708374149"
  }'
```

### Transfer to Phone
```bash
curl -X POST https://pals-pay.onrender.com/api/v1/wallet/transfer \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_phone": "254712345678",
    "amount": 100,
    "description": "Test transfer"
  }'
```

### Withdraw
```bash
curl -X POST https://pals-pay.onrender.com/api/v1/wallet/withdraw \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "payment_method_id": 1
  }'
```

---

## Database Verification

### Check User Phone Numbers
```sql
SELECT id, email, phone_number, first_name, last_name 
FROM users 
WHERE email IN ('john.doe@example.com', 'jane.smith@example.com');
```

### Check Wallet Balances
```sql
SELECT w.id, w.balance, w.available_balance, u.email 
FROM wallets w 
JOIN users u ON w.user_id = u.id 
WHERE u.email IN ('john.doe@example.com', 'jane.smith@example.com');
```

### Check Recent Transactions
```sql
SELECT 
  t.id,
  t.transaction_type,
  t.amount,
  t.fee,
  t.status,
  t.created_at,
  sender.email as sender_email,
  receiver.email as receiver_email
FROM transactions t
LEFT JOIN wallets sw ON t.sender_wallet_id = sw.id
LEFT JOIN users sender ON sw.user_id = sender.id
LEFT JOIN wallets rw ON t.receiver_wallet_id = rw.id
LEFT JOIN users receiver ON rw.user_id = receiver.id
ORDER BY t.created_at DESC
LIMIT 10;
```

### Check Transaction Summary
```sql
SELECT 
  transaction_type,
  status,
  COUNT(*) as count,
  SUM(amount) as total_amount
FROM transactions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY transaction_type, status;
```

---

## Common Issues & Solutions

### Issue: Balance not updating
**Solution:** 
- Check if transaction status is 'completed'
- Verify callback URL is correct for M-Pesa
- Check backend logs for errors

### Issue: Analytics showing 0
**Solution:**
- Ensure transactions are within last 30 days
- Check transaction status is 'completed'
- Verify wallet_id matches in transactions table

### Issue: Transfer fails
**Solution:**
- Verify receiver phone exists in database
- Check sender has sufficient balance
- Ensure phone format is correct (254...)

### Issue: M-Pesa callback not received
**Solution:**
- Check ngrok is running (for local testing)
- Verify callback URL in .env
- Check ngrok dashboard: http://localhost:4040
- Restart backend after .env changes

---

## Success Criteria

✅ Balance displays correctly
✅ Analytics show accurate data
✅ Transaction summary updates
✅ M-Pesa deposit works (sandbox)
✅ Transfer between users works
✅ Validations prevent invalid operations
✅ Error messages are clear
✅ Real-time updates work
✅ All transactions recorded in database
✅ Fees calculated correctly

---

## Next Steps After Testing

1. Test with production M-Pesa credentials
2. Add B2C integration for withdrawals
3. Add transaction notifications
4. Add transaction receipts/PDFs
5. Add transaction dispute handling
