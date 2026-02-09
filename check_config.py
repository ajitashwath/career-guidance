"""
Quick Configuration Checker for Career Intelligence Backend

This script checks if your environment is properly configured for testing.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_status(check_name, passed, message=""):
    """Print check status"""
    symbol = "✓" if passed else "✗"
    color_start = "\033[92m" if passed else "\033[91m"
    color_end = "\033[0m"
    print(f"{color_start}{symbol}{color_end} {check_name}")
    if message:
        print(f"  → {message}")

def main():
    print("\n" + "="*80)
    print("  Career Intelligence Backend - Configuration Check")
    print("="*80 + "\n")
    
    # Check .env file
    print("📁 Configuration Files:")
    print_status(
        ".env file exists",
        Path(".env").exists(),
        "Create from .env.example if missing" if not Path(".env").exists() else ""
    )
    print_status(
        ".env.example exists",
        Path(".env.example").exists()
    )
    print()
    
    # Load environment
    if not Path(".env").exists():
        print("⚠️  Cannot check environment variables without .env file")
        print("   Run: copy .env.example .env")
        print("   Then edit .env with your credentials\n")
        return
    
    load_dotenv()
    
    # Check required variables
    print("🔑 Required Configuration:")
    
    required = {
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_KEY": "Supabase service role key",
        "SUPABASE_JWT_SECRET": "JWT secret for token validation",
        "LLM_PROVIDER": "LLM provider (should be 'openrouter')",
        "OPENROUTER_API_KEY": "OpenRouter API key for AI features"
    }
    
    all_required_ok = True
    for var, desc in required.items():
        value = os.getenv(var, "")
        is_set = bool(value and not value.startswith("your-"))
        
        if var == "LLM_PROVIDER":
            is_set = value == "openrouter"
            print_status(
                f"{var}",
                is_set,
                f"Current: {value}, Expected: openrouter" if not is_set else "Correctly set to openrouter"
            )
        else:
            print_status(
                f"{var}",
                is_set,
                desc if not is_set else "Configured"
            )
        
        if not is_set:
            all_required_ok = False
    
    print()
    
    # Check optional test tokens
    print("🧪 Test Tokens (Optional - for comprehensive testing):")
    
    test_tokens = {
        "TEST_STUDENT_TOKEN": "Student role token",
        "TEST_RECRUITER_TOKEN": "Recruiter role token",
        "TEST_ADMIN_TOKEN": "Admin role token"
    }
    
    any_token_set = False
    for var, desc in test_tokens.items():
        value = os.getenv(var, "")
        is_set = bool(value and not value.startswith("your-"))
        
        if is_set:
            any_token_set = True
        
        print_status(
            f"{var}",
            is_set,
            desc if not is_set else "Configured"
        )
    
    print()
    
    # Check Python packages
    print("📦 Python Dependencies:")
    
    try:
        import fastapi
        print_status("FastAPI", True, f"Version: {fastapi.__version__}")
    except ImportError:
        print_status("FastAPI", False, "Not installed - run: pip install -r requirements.txt")
    
    try:
        import uvicorn
        print_status("Uvicorn", True)
    except ImportError:
        print_status("Uvicorn", False, "Not installed")
    
    try:
        import httpx
        print_status("HTTPX", True)
    except ImportError:
        print_status("HTTPX", False, "Not installed")
    
    try:
        import langchain
        print_status("LangChain", True)
    except ImportError:
        print_status("LangChain", False, "Not installed")
    
    print()
    
    # Summary
    print("="*80)
    print("📊 Summary:")
    print("="*80 + "\n")
    
    if all_required_ok:
        print("✅ All required configuration is set!")
        print()
        
        if any_token_set:
            print("✅ Test tokens are configured - you can run comprehensive tests")
        else:
            print("⚠️  No test tokens configured")
            print("   Some tests will be skipped")
            print("   See TESTING_GUIDE.md for how to get test tokens")
        
        print()
        print("🚀 Next steps:")
        print("   1. Start the server:")
        print("      uvicorn app.main:app --reload --port 8000")
        print()
        print("   2. In a separate terminal, run tests:")
        print("      python test_all_endpoints.py")
        print()
        print("   3. Check the results in test_report.json")
        print()
    else:
        print("❌ Configuration incomplete!")
        print()
        print("📝 To fix:")
        print("   1. Edit the .env file")
        print("   2. Add the missing values (marked with ✗ above)")
        print("   3. Run this check again: python check_config.py")
        print()
        print("📚 For help:")
        print("   - See TESTING_README.md for detailed instructions")
        print("   - See TESTING_GUIDE.md for how to get API keys and tokens")
        print()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
