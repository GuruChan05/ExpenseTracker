from database import get_connection


try:
    conn = get_connection()

    print("================================")
    print("SUPABASE CONNECTION SUCCESSFUL")
    print("================================")

    conn.close()

except Exception as error:

    print("================================")
    print("SUPABASE CONNECTION FAILED")
    print("================================")
    print(error)