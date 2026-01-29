"""
Quick validation script
Checks if all Python files have valid syntax
"""

import py_compile
import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

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
    filepath = os.path.join(script_dir, file)
    try:
        py_compile.compile(filepath, doraise=True)
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
