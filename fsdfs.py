import os
import requests
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não foram configuradas!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

url_ogmo = "http://www.ogmo-recife.org.br/EscalaNet/RelatorioResultadoEscala.php"
data_atual = datetime.now().strftime("%d/%m/%Y")

# Lista com os períodos que você deseja buscar
periodos = ["46", "47", "48", "49"]

for periodo in periodos:
    print(f"⏳ Buscando dados do OGMO para a data {data_atual} (Período {periodo})...")
    
    dados_post = {
        "categoria": "01",
        "data": data_atual, 
        "periodo": periodo
    }
    
    resposta = requests.post(url_ogmo, data=dados_post)

    if resposta.status_code == 200:
        html_io = io.StringIO(resposta.text)
        
        try:
            tabelas = pd.read_html(html_io)
            
            if tabelas:
                df = tabelas[0] 
                df = df.fillna("")
                
                # Opcional: Adicionar a coluna de período para identificar de qual turno é o dado
                df["periodo_escala"] = periodo
                
                registros = [{"dados": row} for row in df.to_dict(orient="records")]
                
                print(f"☁️ Salvando dados do período {periodo} no Supabase...")
                response = supabase.table("escala_estiva").upsert(registros).execute()
                print(f"✅ Período {periodo} salvo com sucesso!")
            else:
                print(f"⚠️ Nenhuma tabela encontrada para o período {periodo}.")
                
        except Exception as e:
            print(f"❌ Erro ao processar o período {periodo}: {e}")
    else:
        print(f"❌ Erro de conexão com o OGMO no período {periodo}. Código: {resposta.status_code}")

print("🚀 Processo de varredura de todos os períodos concluído!")