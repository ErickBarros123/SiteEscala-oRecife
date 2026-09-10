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

url_ogmo = "http://www.ogmo-recife.org.br/EscalaNet/RelatorioResultadoEscala.php"
data_atual = datetime.now().strftime("%d/%m/%Y")
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
                
                # Normaliza as colunas para garantir que o front-end encontre Navio, Cais, Operador
                registros_formatados = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    
                    # Padroniza as chaves independentemente de como venham do HTML do OGMO
                    registro_limpo = {
                        "periodo": periodo,
                        "cais": str(row_dict.get("Cais", row_dict.get("CAIS", row_dict.get(0, "-")))),
                        "navio": str(row_dict.get("Navio", row_dict.get("NAVIO", row_dict.get(1, "-")))),
                        "operador": str(row_dict.get("Operador", row_dict.get("OPERADOR", row_dict.get(2, "-"))))
                    }
                    
                    if registro_limpo["navio"] != "-" and registro_limpo["navio"] != "":
                        registros_formatados.append({"dados": registro_limpo})

                if registros_formatados:
                    print(f"☁️ Salvando dados do período {periodo} no Supabase...")
                    supabase.table("escala_estiva").upsert(registros_formatados).execute()
                    print(f"✅ Período {periodo} salvo com sucesso!")
                else:
                    print(f"⚠️ Nenhum registro válido no período {periodo}.")
            else:
                print(f"⚠️ Nenhuma tabela encontrada para o período {periodo}.")
                
        except Exception as e:
            print(f"❌ Erro ao processar o período {periodo}: {e}")
    else:
        print(f"❌ Erro de conexão com o OGMO no período {periodo}.")

print("🚀 Varredura concluída!")