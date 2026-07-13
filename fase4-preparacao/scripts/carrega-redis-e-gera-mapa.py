# ============================================================
# PBL FASE 4 - 4ª ENTREGA: NoSQL (REDIS) + MAPA
# Lê os dados da análise (Q2 - bairros) persistidos no Redis Cloud
# (modelo key-value, RedisJSON) e gera o mapa.html com Folium.
# Aluno: Thiago Fiel de Oliveira | RM 570088 | Grupo DataGuy | FIAP
# Ambiente: Google Colab
# ============================================================

# !pip install redis folium

import redis
import folium
import json

# ------------------------------------------------------------
# Conexão com o Redis Cloud
#   host/port = endpoint do seu banco (a porta é o número após os ':')
#   troque a senha pela real ao rodar (na entrega ela vai mascarada)
# ------------------------------------------------------------
r = redis.Redis(
    host='tray-appliance-cap-84884.db.redis.io',
    port=11986,
    username='default',
    password='SUA_SENHA',          # senha do banco (ocultada na entrega)
    db=0,
    decode_responses=True
)

# Nome da chave criada no Redis Insight
chave = 'pontos_turisticos_bairros_urbaniq'

# ------------------------------------------------------------
# Recupera o JSON persistido no Redis (evidência de persistência)
# ------------------------------------------------------------
dados = r.json().get(chave)

# ------------------------------------------------------------
# Monta o mapa a partir dos dados lidos do Redis
# ------------------------------------------------------------
fiap_lat, fiap_lon = -23.563508, -46.652847
mapa = folium.Map(location=[fiap_lat, fiap_lon], zoom_start=12)

folium.Marker(
    [fiap_lat, fiap_lon],
    popup="<b>FIAP Paulista</b><br>Av. Paulista, 1106<br>São Paulo - SP",
    icon=folium.Icon(color='blue', icon='star')
).add_to(mapa)

for item in dados:
    rk = int(item['RANKING'])
    # 27 pontos: topo (verde) / meio (laranja) / base (vermelho)
    cor = 'green' if rk <= 9 else ('orange' if rk <= 15 else 'red')
    popup = (
        f"<b>{item['NM_PONTO_TURISTICO']}</b><br>"
        f"Bairro: {item['NM_BAIRRO']}<br>"
        f"Ranking: {rk}<br>"
        f"Nota média: {item['MEDIA_NOTA']:.2f}<br>"
        f"Avaliações: {item['QTD_AVALIACOES']}"
    )
    folium.Marker(
        [item['NR_LATITUDE'], item['NR_LONGITUDE']],
        popup=popup,
        icon=folium.Icon(color=cor)
    ).add_to(mapa)

mapa.save('mapa.html')
print("Mapa gerado com sucesso!")

# ------------------------------------------------------------
# OBS: o JSON foi carregado na chave manualmente pelo Redis Insight.
# Para gravar via Python (alternativa), use antes da leitura:
#   with open('pontos_turisticos_bairros_cidade_alfa.json', encoding='utf-8') as f:
#       r.json().set(chave, '$', json.load(f))
# ------------------------------------------------------------
