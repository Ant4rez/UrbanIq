"""Gera o PDF da Fase 6 a partir de relatorio.html.

Requisitos: pip install playwright  e  playwright install chromium
Uso: python gerar_pdf.py

O script tambem confere se o conteudo de alguma pagina passou da area util,
para evitar texto cortado ou escondido no PDF.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

PASTA = Path(__file__).parent
HTML = PASTA / "relatorio.html"
PDF = PASTA.parent / "entregaveis" / "DataGuy_PBL_Fase_6.pdf"

CONFERE_ESTOURO = """
() => [...document.querySelectorAll('.pagina')].map((p, i) => {
    const rodape = p.querySelector('.rodape');
    const limite = rodape ? rodape.getBoundingClientRect().top : p.getBoundingClientRect().bottom;
    let base = 0;
    for (const el of p.children) {
        if (el === rodape || getComputedStyle(el).position === 'absolute') continue;
        base = Math.max(base, el.getBoundingClientRect().bottom);
    }
    return { pagina: i + 1, folga_px: Math.round(limite - base) };
})
"""

with sync_playwright() as p:
    navegador = p.chromium.launch()
    pagina = navegador.new_page()
    pagina.goto(HTML.as_uri())
    pagina.wait_for_load_state("networkidle")
    for item in pagina.evaluate(CONFERE_ESTOURO):
        situacao = "ok" if item["folga_px"] >= 8 else "ESTOUROU"
        print(f"pagina {item['pagina']:>2}: folga de {item['folga_px']:>4}px  {situacao}")
    PDF.parent.mkdir(exist_ok=True)
    pagina.pdf(path=str(PDF), format="A4", print_background=True, prefer_css_page_size=True)
    navegador.close()
print(f"PDF gerado em {PDF}")
