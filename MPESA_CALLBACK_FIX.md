# M-Pesa Sandbox Callback Issue - SOLUTION

## 🔴 Problem
You made deposits but wallet shows 0 because:
- M-Pesa sandbox sends callback to the URL in your `.env`
- Callback updates the wallet balance
- If callback fails, transaction stays "pending" and balance doesn't update

## ✅ Quick Fix Options

### Option 1: Check Database Directly (Fastest)
Run this SQL to see if transactions exist:

```sql
-- Check your transactions
SELECT 
  id,
  transaction_type,
  amount,
  status,
  created_at,
  metadata
FROM transactions
WHERE receiver_wallet_id IN (
  SELECT id FROM wallets WHERE user_id = (
    SELECT id FROM users WHERE email = 'kiplangatkevin335@gmail.com'
  )
)
ORDER BY created_at DESC
LIMIT 5;
```

**If you see transactions with status='pending':**
- Callback never reached your backend
- Need to manually complete them (see Option 3)

**If you see no transactions:**
- Deposit request failed
- Check backend logs on Render

---

### Option 2: Manually Complete Pending Deposits
If you have pending transactions, run this SQL to complete them:

```sql
-- Get your wallet ID first
SELECT w.id, w.balance, u.email 
FROM wallets w 
JOIN users u ON w.user_id = u.id 
WHERE u.email = 'kiplangatkevin335@gmail.com';

-- Complete pending deposits (replace WALLET_ID with your wallet ID)
UPDATE transactions 
SET status = 'completed'
WHERE receiver_wallet_id = WALLET_ID 
  AND transaction_type = 'deposit'
  AND status = 'pending';

-- Update wallet balance (replace WALLET_ID and AMOUNT)
UPDATE wallets 
SET balance = balance + (
  SELECT COALESCE(SUM(amount), 0) 
  FROM transactions 
  WHERE receiver_wallet_id = WALLET_ID 
    AND transaction_type = 'deposit'
    AND status = 'completed'
) - balance
WHERE id = WALLET_ID;
```

---

### Option 3: Add Manual Deposit Endpoint (For Testing)
Since sandbox callbacks are unreliable, add a test endpoint to manually complete deposits.

**Add to `wallet_routes.py`:**

```python
@wallet_bp.route('/deposit/manual', methods=['POST'])
@token_required
def manual_deposit(current_user):
    """Manual deposit for testing (sandbox only)"""
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'message': 'Amount required'}), 400
    
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return jsonify({'message': 'Amount must be positive'}), 400
    except:
        return jsonify({'message': 'Invalid amount'}), 400
    
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    try:
        # Create completed transaction
        transaction = Transaction(
            receiver_wallet_id=wallet.id,
            amount=amount,
            net_amount=amount,
            transaction_type=TransactionType.deposit,
            status=TransactionStatus.completed,
            provider=PaymentProvider.mpesa,
            description="Manual test deposit",
            metadata={'manual': True}
        )
        
        db.session.add(transaction)
        
        # Update wallet
        wallet.balance += amount
        wallet.available_balance += amount
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Manual deposit successful',
            'new_balance': float(wallet.balance)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Deposit failed: {str(e)}'}), 500
```

Then test with:
```bash
curl -X POST https://pals-pay.onrender.com/api/v1/wallet/deposit/manual \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'
```

---

### Option 4: Check Callback URL Configuration

**On Render Dashboard:**
1. Go to your backend service
2. Click "Environment"
3. Check `MPESA_CALLBACK_URL` value

**Should be:**
```
MPESA_CALLBACK_URL=https://pals-pay.onrender.com/api/v1/mpesa/callback
```

**NOT:**
```
MPESA_CALLBACK_URL=http://localhost:5000/api/v1/mpesa/callback
MPESA_CALLBACK_URL=https://abc123.ngrok.io/api/v1/mpesa/callback
```

---

## 🔍 Diagnostic Steps

### 1. Check Backend Logs
On Render dashboard:
- Go to your service
- Click "Logs" tab
- Look for M-Pesa callback logs
- Search for: "M-Pesa STK Callback"

### 2. Check Transaction Status
```sql
SELECT status, COUNT(*) 
FROM transactions 
GROUP BY status;
```

### 3. Test Callback Endpoint Directly
```bash
curl -X POST https://pals-pay.onrender.com/api/v1/mpesa/callback \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "ResultCode": 0,
        "CheckoutRequestID": "test123"
      }
    }
  }'
```

Should return: `{"ResultCode": 0, "ResultDesc": "Accepted"}`

---

## 🎯 Recommended Solution for School Project

**Use Manual Deposit Endpoint:**
1. Add the manual deposit endpoint (Option 3)
2. Deploy to Render
3. Use it for testing instead of real M-Pesa
4. For demo, show the M-Pesa integration code

**Why?**
- Sandbox callbacks are unreliable
- No need for ngrok in production
- Faster testing
- Same database logic as real deposits

---

## 📊 Quick Balance Check

Run this to see your current balance:

```sql
SELECT 
  u.email,
  w.balance,
  w.available_balance,
  (SELECT COUNT(*) FROM transactions WHERE receiver_wallet_id = w.id) as total_transactions,
  (SELECT COUNT(*) FROM transactions WHERE receiver_wallet_id = w.id AND status = 'pending') as pending_transactions
FROM wallets w
JOIN users u ON w.user_id = u.id
WHERE u.email = 'kiplangatkevin335@gmail.com';
```

---

## 🚀 Next Steps

1. **Check database** - See if transactions exist
2. **If pending** - Manually complete them (Option 2)
3. **For future testing** - Add manual deposit endpoint (Option 3)
4. **For production** - Fix callback URL and use real M-Pesa

Let me know what you find in the database!
