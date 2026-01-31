from flask import Blueprint, request, jsonify
from sqlalchemy import Transaction, func
from models import User, Wallet, Transaction
from extensions import db
from server.auth.decorators import token_required, role_required
from datetime import datetime, timedelta



admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin') # Define the admin blueprint

#admin can get all users
@admin_bp.route("/users", methods=["GET"])
@token_required
@role_required("admin")
def get_all_users():
    users = User.query.all()

    data = []
    for user in users:
        data.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at
        })

    return jsonify(data), 200

#activate or deactivate a user
@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@token_required
@role_required("admin")
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)  
    data = request.get_json()

    if 'is_active' not in data:
        return jsonify({"message": "Missing 'is_active' field"}), 400
    
    user.is_active = data['is_active']
    db.session.commit()

    return jsonify({"message": f"User {'activated' if user.is_active else 'deactivated'} successfully."}), 200

#view all wallets and their details
@admin_bp.route("/wallets", methods=["GET"])
@token_required
@role_required("admin")
def get_all_wallets():
    wallets = Wallet.query.all()

    data = []
    for wallet in wallets:
        data.append({
            "user_id": wallet.user_id,
            "balance": float(wallet.balance),
            "currency": wallet.currency,
            "updated_at": wallet.updated_at
        })

    return jsonify(data), 200


#view all transactions
@admin_bp.route("/transactions", methods=["GET"])
@token_required
@role_required("admin")
def get_all_transactions():
    transactions = Transaction.query.all()

    data = []
    for tx in transactions:
        data.append({
            "id": tx.id,
            "user_id": tx.user_id,
            "amount": float(tx.amount),
            "type": tx.type,
            "status": tx.status,(No title)

            "timestamp": tx.timestamp
        })

    return jsonify(data), 200

#view system statistics
@admin_bp.route("/stats", methods=["GET"])
@token_required
@role_required("admin")
def get_system_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_wallets = Wallet.query.count()
    total_transactions = Transaction.query.count()
    total_volume = db.session.query(func.sum(Transaction.amount)).scalar() or 0
    daily_profit = db.session.query(func.sum(Transaction.fee)).filter(Transaction.status == "completed", Transaction.timestamp >= datetime.utcnow().date()).scalar() or 0  # Assuming there's a 'fee' field in Transaction model, it checks for completed transactions today

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "total_wallets": total_wallets,
        "total_transactions": total_transactions,
        "total_transaction_volume": float(total_volume),
        "daily_profit": float(daily_profit)
    }

    return jsonify(stats), 200


#transactional reversal
@admin_bp.route("/transactions/<int:tx_id>/reverse", methods=["POST"])
@token_required
@role_required("admin")
def reverse_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)

    if tx.status != "completed":
        return jsonify({"message": "Only completed transactions can be reversed."}), 400

    sender_wallet = Wallet.query.filter_by(user_id=tx.user_id).first()
    receiver_wallet = Wallet.query.filter_by(user_id=tx.receiver_id).first()  #

    if receiver_wallet.balance < tx.amount:  
        return jsonify({"message": "Insufficient funds in receiver's wallet to reverse the transaction."}), 400
    
    #reversals
    sender_wallet.balance += tx.amount  # Add amount back to sender
    receiver_wallet.balance -= tx.amount  # Deduct amount from receiver

    tx.status = "reversed"
    db.session.commit()

    return jsonify({"message": "Transaction reversed successfully."}), 200


#tracking suspicious activities
@admin_bp.route("/transactions/suspicious", methods=["GET"])
@token_required
@role_required("admin")
def get_suspicious_transactions():
    last_24_hours = datetime.utcnow() - timedelta(hours=24) # Get the timestamp for 24 hours ago for when the admin wants to track suspicious activities in the last 24 hours
    threshold_amount = 100000  # Define a threshold amount for suspicious transactions
    suspicious_txs = Transaction.query.filter(Transaction.amount >= threshold_amount, Transaction.timestamp >= last_24_hours).all()

    data = []
    for tx in suspicious_txs: #tx = transaction
        data.append({
            "id": tx.id,
            "user_id": tx.user_id,
            "amount": float(tx.amount),
            "type": tx.type,
            "status": tx.status,
            "timestamp": tx.timestamp
        })

    return jsonify(data), 200

#flag a transaction as suspicious
@admin_bp.route("/transactions/<int:tx_id>/flag", methods=["POST"])
@token_required
@role_required("admin")
def flag_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)  # Get the transaction or return 404

    tx.is_suspicious = True  # Assuming there's an 'is_suspicious' boolean field in Transaction model
    db.session.commit()

    return jsonify({"message": "Transaction flagged as suspicious."}), 200


#analytics and profit trends
@admin_bp.route("/analytics", methods=["GET"])
@token_required
@role_required("admin")
def get_analytics():
    #for a week
    today = datetime.utcnow().date()  # Get today's date
    week_ago = today - timedelta(days=7)  # Date a week ago

    daily_stats = db.session.query(
        func.date(Transaction.timestamp).label("date"),
        func.sum(Transaction.amount).label("total_amount"),
        func.sum(Transaction.fee).label("total_fee")
    ).filter(Transaction.timestamp >= week_ago).group_by(func.date(Transaction.timestamp)).all()

    # Format the data
    analytics_data = []
    for stat in daily_stats:
        analytics_data.append({
            "date": stat.date,
            "total_amount": float(stat.total_amount),
            "total_fee": float(stat.total_fee)
        })

    return jsonify(analytics_data), 200