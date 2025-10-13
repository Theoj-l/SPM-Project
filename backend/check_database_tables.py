#!/usr/bin/env python3
"""
Script to check if the required database tables exist
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def check_tables():
    """Check if required tables exist"""
    try:
        # Initialize Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment")
            return False
            
        supabase: Client = create_client(url, key)
        
        # Check if tables exist by trying to query them
        tables_to_check = [
            "task_comments",
            "subtasks", 
            "task_files"
        ]
        
        print("🔍 Checking database tables...")
        
        for table in tables_to_check:
            try:
                # Try to query the table (limit 0 to just check if it exists)
                result = supabase.table(table).select("*").limit(0).execute()
                print(f"✅ Table '{table}' exists")
            except Exception as e:
                print(f"❌ Table '{table}' does not exist or has issues: {e}")
                
        # Check if we can query the main tables
        try:
            result = supabase.table("tasks").select("id").limit(1).execute()
            print("✅ Table 'tasks' exists")
        except Exception as e:
            print(f"❌ Table 'tasks' has issues: {e}")
            
        try:
            result = supabase.table("users").select("id").limit(1).execute()
            print("✅ Table 'users' exists")
        except Exception as e:
            print(f"❌ Table 'users' has issues: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    check_tables()
