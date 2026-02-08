
import os
from dotenv import load_dotenv
from supabase import create_client

def test_connection():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"Testing connection to: {url}")
    try:
        supabase = create_client(url, key)
        # Try to list tables or get some basic info
        # Using a simple query that should work if key/url are valid
        response = supabase.table("students").select("count", count="exact").limit(1).execute()
        print("SUCCESS: Connection successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"ERROR: Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
