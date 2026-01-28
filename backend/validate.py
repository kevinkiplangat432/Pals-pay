"""
Quick validation script
Checks if all Python files have valid syntax
"""

import py_compile
import os
import sys

files_to_check = [
    'app.py',
    'config.py',
    'database.py',
    'extensions.py',
    'manage.py',
    'models/__init__.py',
    'models/user.py',
    'models/wallet.py',
    'models/transaction.py',
    'models/beneficiary.py',
]

print("Validating Python files...\n")

all_valid = True
for file in files_to_check:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✓ {file}")
    except py_compile.PyCompileError as e:
        print(f"✗ {file}: {e}")
        all_valid = False

print()
if all_valid:
    print("✅ All files have valid Python syntax!")
    sys.exit(0)
else:
    print("❌ Some files have syntax errors")
    sys.exit(1)
