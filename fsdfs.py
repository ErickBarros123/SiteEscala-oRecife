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
data_iso = datetime.now().strftime("%Y-%m-%d") # Formato YYYY-MM-DD para bater com a URL
periodos = {"46": "1", "47": "2", "48": "3", "49": "4"} # Mapeia os períodos para os turnos 1, 2, 3, 4

for periodo, turno_num in periodos.items():
    print(f"⏳ Buscando dados do OGMO para a data {data_atual} (Período {periodo} / Turno {turno_num})...")
    
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
                
                registros_formatados = []
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    
                    registro_limpo = {
                        "data": data_iso, # Salva a data limpa (ex: 2026-09-10)
                        "turno": turno_num, # Salva o número do turno (1, 2, 3, 4)
                        "cais": str(row_dict.get("Cais", row_dict.get("CAIS", row_dict.get(0, "-")))),
                        "navio": str(row_dict.get("Navio", row_dict.get("NAVIO", row_dict.get(1, "-")))),
                        "operador": str(row_dict.get("Operador", row_dict.get("OPERADOR", row_dict.get(2, "-"))))
                    }
                    
                    if registro_limpo["navio"] != "-" and registro_limpo["navio"] != "":
                        registros_formatados.append({"dados": registro_limpo})

                if registros_formatados:
                    print(f"☁️ Salvando dados do Turno {turno_num} no Supabase...")
                    supabase.table("escala_estiva").upsert(registros_formatados).execute()
                    print(f"✅ Turno {turno_num} salvo com sucesso!")
                else:
                    print(f"⚠️ Nenhum registro válido no Turno {turno_num}.")
            else:
                print(f"⚠️ Nenhuma tabela encontrada para o período {periodo}.")
                
        except Exception as e:
            print(f"❌ Erro ao processar o período {periodo}: {e}")
    else:
        print(f"❌ Erro de conexão com o OGMO no período {periodo}.")

print("🚀 Varredura concluída!")