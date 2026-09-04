# core/supabase_client.py
from supabase import create_client, Client

# Вставь сюда данные, которые ты сохранила на Шаге 1:
SUPABASE_URL = "https://grbyodinibuigmjtxntr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdyYnlvZGluaWJ1aWdtanR4bnRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzk1MTEsImV4cCI6MjEwMjY1NTUxMX0.-PUlOifqgGn_Rzh5z4wZNl94v4k2oVh66tP_YmOwvlk"

# Инициализируем клиент Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)