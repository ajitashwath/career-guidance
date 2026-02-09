"""
Quick Setup and Test Runner for Career Intelligence Backend

This script helps you:
1. Check prerequisites
2. Set up .env file
3. Start the server
4. Run comprehensive endpoint tests
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("Checking Prerequisites")
    
    checks = {
        "Python 3.11+": sys.version_info >= (3, 11),
        ".env file": Path(".env").exists(),
        "requirements.txt": Path("requirements.txt").exists(),
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    return all_passed

def setup_env():
    """Help user set up .env file"""
    print_header("Environment Setup")
    
    if Path(".env").exists():
        print("  ℹ .env file already exists")
        response = input("\n  Do you want to review/edit it? (y/n): ")
        if response.lower() == 'y':
            if sys.platform == 'win32':
                os.system("notepad .env")
            else:
                os.system("nano .env")
        return True
    
    if not Path(".env.example").exists():
        print("  ✗ .env.example not found!")
        return False
    
    print("  Creating .env from .env.example...")
    
    # Copy .env.example to .env
    with open(".env.example", "r") as source:
        content = source.read()
    
    with open(".env", "w") as target:
        target.write(content)
    
    print("  ✓ .env file created")
    print("\n  ⚠ IMPORTANT: You need to configure the following in .env:")
    print("     - SUPABASE_URL")
    print("     - SUPABASE_KEY")
    print("     - SUPABASE_JWT_SECRET")
    print("     - OPENROUTER_API_KEY (for AI features)")
    print("     - Test tokens (TEST_STUDENT_TOKEN, etc.) for testing")
    
    response = input("\n  Open .env file for editing now? (y/n): ")
    if response.lower() == 'y':
        if sys.platform == 'win32':
            os.system("notepad .env")
        else:
            os.system("nano .env")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    response = input("  Install/Update Python dependencies? (y/n): ")
    if response.lower() != 'y':
        print("  Skipping dependency installation")
        return True
    
    try:
        print("\n  Installing dependencies from requirements.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ Dependencies installed successfully")
            return True
        else:
            print(f"  ✗ Installation failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error installing dependencies: {e}")
        return False

def check_env_variables():
    """Check if critical environment variables are set"""
    print_header("Checking Environment Variables")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        "SUPABASE_URL": "Supabase Database URL",
        "SUPABASE_KEY": "Supabase Service Key",
        "SUPABASE_JWT_SECRET": "JWT Secret",
        "OPENROUTER_API_KEY": "OpenRouter API Key (for AI)",
    }
    
    optional_vars = {
        "TEST_STUDENT_TOKEN": "Student test token",
        "TEST_RECRUITER_TOKEN": "Recruiter test token",
        "TEST_ADMIN_TOKEN": "Admin test token",
    }
    
    print("  Required Variables:")
    all_required_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}":
            print(f"    ✓ {var}: Configured")
        else:
            print(f"    ✗ {var}: NOT SET - {description}")
            all_required_set = False
    
    print("\n  Optional Variables (for testing):")
    any_test_token = False
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}":
            print(f"    ✓ {var}: Configured")
            any_test_token = True
        else:
            print(f"    ⊘ {var}: Not set - {description}")
    
    if not all_required_set:
        print("\n  ⚠ Some required variables are not configured!")
        print("  Please edit .env and add the missing values.")
        return False
    
    if not any_test_token:
        print("\n  ℹ No test tokens configured. Some tests will be skipped.")
        print("  See TESTING_GUIDE.md for how to get test tokens.")
    
    return True

def start_server():
    """Start the backend server"""
    print_header("Starting Backend Server")
    
    print("  Server will start at http://localhost:8000")
    print("  API docs will be available at http://localhost:8000/docs")
    print("\n  Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
            cwd=os.getcwd()
        )
    except KeyboardInterrupt:
        print("\n\n  Server stopped")

def run_tests():
    """Run the comprehensive test suite"""
    print_header("Running Comprehensive Tests")
    
    if not Path("test_all_endpoints.py").exists():
        print("  ✗ test_all_endpoints.py not found!")
        return False
    
    try:
        print("  Starting test execution...\n")
        result = subprocess.run(
            [sys.executable, "test_all_endpoints.py"],
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("\n  ✓ Tests completed successfully")
            print("  Check test_report.json for detailed results")
            return True
        else:
            print("\n  ⚠ Some tests may have failed")
            print("  Check test_report.json for details")
            return False
    except Exception as e:
        print(f"  ✗ Error running tests: {e}")
        return False

def main():
    """Main menu"""
    print("\n" + "="*80)
    print("  Career Intelligence Backend - Quick Setup & Test")
    print("="*80)
    
    while True:
        print("\n  What would you like to do?")
        print("  1. Check prerequisites")
        print("  2. Set up .env file")
        print("  3. Install dependencies")
        print("  4. Check environment variables")
        print("  5. Start backend server")
        print("  6. Run comprehensive tests (server must be running separately)")
        print("  7. Exit")
        
        choice = input("\n  Enter your choice (1-7): ").strip()
        
        if choice == "1":
            check_prerequisites()
        elif choice == "2":
            setup_env()
        elif choice == "3":
            install_dependencies()
        elif choice == "4":
            check_env_variables()
        elif choice == "5":
            start_server()
        elif choice == "6":
            print("\n  ⚠ Make sure the server is running in a separate terminal!")
            response = input("  Continue with tests? (y/n): ")
            if response.lower() == 'y':
                run_tests()
        elif choice == "7":
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            print("\n  Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Goodbye!\n")
        sys.exit(0)
