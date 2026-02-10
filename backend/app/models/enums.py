import enum  


class TransactionStatus(enum.Enum):
    #Transaction lifecycle states
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    reversed = "reversed"


class TransactionType(enum.Enum):
    #Types of financial transactions
    transfer = "transfer"
    deposit = "deposit"
    withdrawal = "withdrawal"
    fee = "fee"


class KYCStatus(enum.Enum):
    #KYC verification states
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class WalletStatus(enum.Enum):
    #Wallet operational states
    active = "active"
    frozen = "frozen"
    suspended = "suspended"
    closed = "closed"


class PaymentProvider(enum.Enum):
    #Payment service providers
    internal = "internal"
    mpesa = "mpesa"
    bank = "bank"
    card = "card"


class DocumentType(enum.Enum):
    #Supported KYC document types
    national_id = "national_id"
    passport = "passport"
    driver_license = "driver_license"
    alien_card = "alien_card"