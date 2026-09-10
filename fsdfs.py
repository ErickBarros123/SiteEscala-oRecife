import os
import requests
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"DEBUG - SUPABASE_URL recebida: '{SUPABASE_URL}'")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não foram configuradas corretamente!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)