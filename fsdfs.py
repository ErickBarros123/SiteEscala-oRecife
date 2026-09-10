import os
import requests
import pandas as pd
import io
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ As variáveis SUPABASE_URL e SUPABASE_KEY não foram configuradas!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Data atual no formato YYYY-MM-DD exigido pelo novo site do Suape
data_atual = datetime.now().strftime("%Y-%m-%d")

# Turnos que deseja consultar (ex: 1, 2, 3, etc.)
turnos = ["1", "2", "3", "4"]

for turno in turnos:
    url_suape = f"http://tpa.ogmosuape.com.br/web/listagem_turno?d={data_atual}&t={turno}"
    print(f"⏳ Buscando dados do OGMO Suape para a data {data_atual} (Turno {turno})...")
    
    # Como o novo endpoint utiliza GET com parâmetros na URL
    resposta = requests.get(url_suape)

    if resposta.status_code == 200:
        html_io = io.StringIO(resposta.text)
        
        try:
            tabelas = pd.read_html(html_io)
            
            if tabelas:
                df = tabelas[0] 
                df = df.fillna("")
                
                registros_formatados = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    
                    # Padroniza as chaves para salvar no Supabase
                    registro_limpo = {
                        "periodo": f"Turno {turno}",
                        "cais": str(row_dict.get("Cais", row_dict.get("CAIS", row_dict.get(0, "-")))),
                        "navio": str(row_dict.get("Navio", row_dict.get("NAVIO", row_dict.get(1, "-")))),
                        "operador": str(row_dict.get("Operador", row_dict.get("OPERADOR", row_dict.get(2, "-"))))
                    }
                    
                    if registro_limpo["navio"] != "-" and registro_limpo["navio"] != "":
                        registros_formatados.append({"dados": registro_limpo})

                if registros_formatados:
                    print(f"☁️ Salvando dados do Turno {turno} no Supabase...")
                    supabase.table("escala_estiva").upsert(registros_formatados).execute()
                    print(f"✅ Turno {turno} salvo com sucesso!")
                else:
                    print(f"⚠️ Nenhum registro válido no Turno {turno}.")
            else:
                print(f"⚠️ Nenhuma tabela encontrada para o Turno {turno}.")
                
        except Exception as e:
            print(f"❌ Erro ao processar o Turno {turno}: {e}")
    else:
        print(f"❌ Erro de conexão com o OGMO Suape no Turno {turno}. Código: {resposta.status_code}")

print("🚀 Varredura do Suape concluída!")