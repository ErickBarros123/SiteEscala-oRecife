import requests
import pandas as pd
import io
import os
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO SUPABASE ---
# Puxa diretamente do ambiente seguro do GitHub Actions
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não foram configuradas!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

url_ogmo = "http://www.ogmo-recife.org.br/EscalaNet/RelatorioResultadoEscala.php"

# Pega a data atual formatada (DD/MM/AAAA) para a requisição
data_atual = datetime.now().strftime("%d/%m/%Y")

dados_post = {
    "categoria": "01",
    "data": data_atual, 
    "periodo": "46"
}

print(f"⏳ Batendo na porta secreta do OGMO para a data {data_atual}...")
resposta = requests.post(url_ogmo, data=dados_post)

if resposta.status_code == 200:
    print("⚙️ Processando a escala...")
    html_io = io.StringIO(resposta.text)
    
    try:
        tabelas = pd.read_html(html_io)
        
        if tabelas:
            df = tabelas[0] 
            df = df.fillna("")
            
            # Formata cada linha como um objeto JSON para salvar na coluna 'dados'
            registros = [{"dados": row} for row in df.to_dict(orient="records")]
            
            print("☁️ Salvando dados no Supabase...")
            response = supabase.table("escala_estiva").upsert(registros).execute()
            
            print("✅ Sucesso Absoluto! Dados enviados para o Supabase e prontos para a Vercel!")
        else:
            print("⚠️ Nenhuma tabela HTML encontrada para esta data/período.")
            
    except Exception as e:
        print(f"❌ Erro ao processar ou enviar os dados: {e}")
else:
    print(f"❌ Erro de conexão com o OGMO. Código: {resposta.status_code}")