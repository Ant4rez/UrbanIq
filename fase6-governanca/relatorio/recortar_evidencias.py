"""Recorta as capturas do SQL Developer para o relatorio da Fase 6.

Remove os paineis laterais (Conexoes e Relatorios) e as areas vazias,
deixando apenas o comando executado e o resultado. Quando a captura tem
outras consultas entre o comando e o resultado, o recorte junta as duas
faixas (comando em cima, resultado embaixo). As capturas originais em
../evidencias/ nao sao alteradas.

Uso: python recortar_evidencias.py
"""
from pathlib import Path
from PIL import Image

ORIGEM = Path(__file__).parent.parent / "evidencias"
DESTINO = Path(__file__).parent / "img"

# nome do recorte: (captura original, [faixas (esquerda, topo, direita, base)])
RECORTES = {
    "01-origens-carregadas": ("01.png", [(348, 352, 1420, 452), (348, 585, 1420, 700)]),
    "02-antes-v1":           ("02.png", [(348, 586, 1916, 1012)]),
    "03-carga-v2":           ("03.png", [(348, 88, 1200, 950)]),
    "04-depois-v2":          ("04.png", [(348, 586, 1916, 1012)]),
    "05-conferencia":        ("05.png", [(348, 208, 1260, 404), (348, 585, 1260, 680)]),
    "06-divergencias":       ("06.png", [(348, 208, 1000, 332), (348, 585, 1000, 700)]),
    "07-casos-tratados":     ("07.png", [(348, 236, 1916, 405), (348, 585, 1916, 800)]),
    "08-reexecucao":         ("08.png", [(348, 88, 1200, 975)]),
    "09-view":               ("09.png", [(348, 205, 1100, 980)]),
}

DESTINO.mkdir(exist_ok=True)
for nome, (arquivo, faixas) in RECORTES.items():
    original = Image.open(ORIGEM / arquivo).convert("RGB")
    partes = [original.crop(faixa) for faixa in faixas]
    largura = max(parte.width for parte in partes)
    altura = sum(parte.height for parte in partes)
    recorte = Image.new("RGB", (largura, altura), "white")
    topo = 0
    for parte in partes:
        recorte.paste(parte, (0, topo))
        topo += parte.height
    recorte.save(DESTINO / f"{nome}.png", optimize=True)
    print(f"{arquivo} -> img/{nome}.png {recorte.size}")
