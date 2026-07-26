import os
from dotenv import load_dotenv
from supabase import create_client


# Load environment
load_dotenv()


url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


print("SUPABASE URL:")
print(url)


print("\nSUPABASE KEY:")
print(key[:20])


# Connect Supabase

supabase = create_client(
    url,
    key
)


print("\nConnected to Supabase")


# Test table

try:

    response = supabase.table(
        "applications"
    ).select("*").execute()


    print("\nDATABASE RESPONSE:")

    print(
        response.data
    )


except Exception as e:

    print("\nDATABASE ERROR:")

    print(e)