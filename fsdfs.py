import os
import requests
import pandas as pd
import io
import time
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ As variáveis SUPABASE_URL e SUPABASE_KEY não foram configuradas!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
url_ogmo = "http://www.ogmo-recife.org.br/EscalaNet/RelatorioResultadoEscala.php"

periodos_map = {
    "46": "1",  # 08h às 14h
    "47": "2",  # 14h às 20h
    "48": "3",  # 20h às 02h
    "49": "4"   # 02h às 08h
}

dias_retroativos = 60

for i in range(dias_retroativos):
    data_alvo = datetime.now() - timedelta(days=i)
    data_formatada = data_alvo.strftime("%d/%m/%Y")
    data_iso = data_alvo.strftime("%Y-%m-%d")
    
    print(f"\n📅 Processando data: {data_formatada} ({i+1}/{dias_retroativos})")

    for periodo, turno_num in periodos_map.items():
        dados_post = {
            "categoria": "01",
            "data": data_formatada, 
            "periodo": periodo
        }
        
        try:
            resposta = requests.post(url_ogmo, data=dados_post, timeout=10)

            if resposta.status_code == 200:
                html_io = io.StringIO(resposta.text)
                tabelas = pd.read_html(html_io)
                
                if tabelas:
                    df = tabelas[0].fillna("")
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
                        supabase.table("escala_estiva").upsert(registros_formatados).execute()
                        print(f"  -> Turno {turno_num} salvo com sucesso.")
        except Exception as e:
            continue

        # Pausa de 2.5 segundos entre cada requisição para o servidor do OGMO respirar sossegado (totalizando uns minutinhos de descanso para você e zero chances de estresse com bloqueio)
        time.sleep(2.5)

print("\n🚀 Carga histórica concluída com sucesso!")