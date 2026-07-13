# ============================================================
# PBL FASE 4 - 3ª ENTREGA: ANÁLISE EXPLORATÓRIA COM PYTHON
# Pergunta Q2: "Determinados bairros da cidade Alfa concentram
#               avaliações mais altas dos pontos turísticos?"
# Aluno: Thiago Fiel de Oliveira | RM 570088 | FIAP
# Ambiente sugerido: Google Colab
# Entrada: avaliacao_bairros_cidade_alfa.csv (gerado na 2ª entrega)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1) LEITURA DO CSV (separador ';' e decimal ',', como exportado do Oracle)
df = pd.read_csv('avaliacao_bairros_cidade_alfa.csv', sep=';', decimal=',')
print(df.head())
print(df.info())
print(df.describe())

# 2) TIPAGEM das colunas de data e nota
df['DT_AVALIACAO'] = pd.to_datetime(df['DT_AVALIACAO'], dayfirst=True, errors='coerce')
df['NR_NOTA_AVALIACAO'] = pd.to_numeric(df['NR_NOTA_AVALIACAO'], errors='coerce')

# 3) QUALIDADE DOS DADOS — identificar inconsistências (exigência do enunciado)
print('\nValores nulos por coluna:')
print(df.isnull().sum())
print('Notas negativas (inválidas):', df[df['NR_NOTA_AVALIACAO'] < 0].shape[0])

# 4) LIMPEZA — remover notas missing e negativas
linhas_antes = len(df)
df = df.dropna(subset=['NR_NOTA_AVALIACAO'])
df = df[df['NR_NOTA_AVALIACAO'] >= 0]
print(f'\nLinhas removidas na limpeza: {linhas_antes - len(df)} | restantes: {len(df)}')

# 5) RESPOSTA DA PERGUNTA — média de nota por BAIRRO + ranking
df_bairro = (df.groupby('NM_BAIRRO')
               .agg(MEDIA_NOTA=('NR_NOTA_AVALIACAO', 'mean'),
                    QTD_AVALIACOES=('NR_NOTA_AVALIACAO', 'size'),
                    QTD_PONTOS=('NM_PONTO_TURISTICO', 'nunique'),
                    PRECO_MEDIO=('VL_PRECO_UNITARIO', 'mean'))
               .reset_index()
               .sort_values('MEDIA_NOTA', ascending=False))
df_bairro['RANKING'] = df_bairro['MEDIA_NOTA'].rank(ascending=False, method='dense').astype(int)
media_global = df['NR_NOTA_AVALIACAO'].mean()
print(f'\nMédia global de avaliação: {media_global:.3f}')
print(df_bairro.round(3).to_string(index=False))

# 6) AGREGAÇÃO POR PONTO TURÍSTICO (com lat/long, para o mapa do 3º desafio)
df_pontos = (df.groupby(['NM_PONTO_TURISTICO', 'NM_BAIRRO'])
               .agg(NR_LATITUDE=('NR_LATITUDE', 'first'),
                    NR_LONGITUDE=('NR_LONGITUDE', 'first'),
                    MEDIA_NOTA=('NR_NOTA_AVALIACAO', 'mean'),
                    PRECO_MEDIO=('VL_PRECO_UNITARIO', 'mean'),
                    QTD_AVALIACOES=('NR_NOTA_AVALIACAO', 'size'))
               .reset_index()
               .sort_values('MEDIA_NOTA', ascending=False))
df_pontos['RANKING'] = df_pontos['MEDIA_NOTA'].rank(ascending=False, method='dense').astype(int)

# 7) VISUALIZAÇÃO — nota média por bairro
plt.figure(figsize=(10, 8))
cores = ['#1a9850' if v >= media_global else '#d73027' for v in df_bairro['MEDIA_NOTA']]
plt.barh(df_bairro['NM_BAIRRO'], df_bairro['MEDIA_NOTA'], color=cores)
plt.axvline(media_global, color='#333', ls='--', lw=1, label=f'Média global = {media_global:.2f}')
plt.gca().invert_yaxis()
plt.xlabel('Nota média (NPS 1-10)')
plt.title('Nota média dos pontos turísticos por bairro — Cidade Alfa')
plt.legend(); plt.tight_layout()
plt.savefig('grafico_media_por_bairro.png', dpi=130)
plt.show()

# 8) GERAÇÃO DO JSON para o NoSQL (Redis) — por ponto turístico, com coordenadas
df_pontos.round(3).to_json('pontos_turisticos_bairros_cidade_alfa.json',
                           orient='records', force_ascii=False)
df_bairro.round(3).to_json('resultado_bairros_cidade_alfa.json',
                           orient='records', force_ascii=False)
print('\nArquivos JSON gerados para persistência no Redis.')
