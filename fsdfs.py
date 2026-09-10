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
data_iso = datetime.now().strftime("%Y-%m-%d")

# Mapeamento correto dos períodos do OGMO Recife para os números dos turnos
periodos_map = {
    "46": "1",  # 08h às 14h
    "47": "2",  # 14h às 20h
    "48": "3",  # 20h às 02h
    "49": "4"   # 02h às 08h
}

for periodo, turno_num in periodos_map.items():
    print(f"⏳ Buscando Período OGMO {periodo} (Turno {turno_num}) para a data {data_atual}...")
    
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
                        "data": data_iso,
                        "turno": turno_num,
                        "cais": str(row_dict.get("Cais", row_dict.get("CAIS", row_dict.get(0, "-")))),
                        "navio": str(row_dict.get("Navio", row_dict.get("NAVIO", row_dict.get(1, "-")))),
                        "operador": str(row_dict.get("Operador", row_dict.get("OPERADOR", row_dict.get(2, "-"))))
                    }
                    
                    if registro_limpo["navio"] != "-" and registro_limpo["navio"] != "":
                        registros_formatados.append({"dados": registro_limpo})

                if registros_formatados:
                    print(f"☁️ Salvando Turno {turno_num} no Supabase...")
                    supabase.table("escala_estiva").upsert(registros_formatados).execute()
                    print(f"✅ Turno {turno_num} salvo!")
                else:
                    print(f"⚠️ Vazio para o período {periodo}.")
            else:
                print(f"⚠️ Sem tabela para o período {periodo}.")
                
        except Exception as e:
            print(f"❌ Erro no período {periodo}: {e}")
    else:
        print(f"❌ Erro HTTP no período {periodo}.")

print("🚀 Sincronização concluída!")