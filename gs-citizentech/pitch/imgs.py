import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
import os

NAVY, TEAL, PINK, TXT, LIGHT, LTEAL, GRAY, BORD = '#1E2A4A', '#12A594', '#ED185C', '#3A4459', '#F3F6FA', '#E3F5F2', '#6B7488', '#D9E1EC'
os.makedirs('img', exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'


def box(ax, x, y, w, h, fc, ec=None, r=0.02, lw=1.2, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec or fc, lw=lw, zorder=z))


def pin(ax, cx, cy, s, color, hole='white'):
    ax.add_patch(Circle((cx, cy), s, fc=color, ec='none', zorder=5))
    ax.add_patch(Polygon([(cx - s * .82, cy - s * .55), (cx + s * .82, cy - s * .55), (cx, cy - s * 2.1)], fc=color, ec='none', zorder=5))
    ax.add_patch(Circle((cx, cy), s * .42, fc=hole, ec='none', zorder=6))


# ---------- LOGO ----------
fig, ax = plt.subplots(figsize=(4, 4), dpi=200)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
fig.patch.set_alpha(0)
pin(ax, .5, .66, .16, TEAL, NAVY)
for dx, c in [(-.1, '#ffffff'), (0, PINK), (.1, '#ffffff')]:
    ax.add_patch(Circle((.5 + dx, .66), .018, fc=c, zorder=7))
ax.text(.5, .25, 'Urban', ha='right', va='center', fontsize=34, fontweight='bold', color='white')
ax.text(.5, .25, 'IQ', ha='left', va='center', fontsize=34, fontweight='bold', color=TEAL)
ax.text(.5, .1, 'zeladoria que escuta todo território', ha='center', fontsize=10, color='#C9D3E6')
plt.savefig('img/logo.png', transparent=True, bbox_inches='tight'); plt.close()

# ---------- ARQUITETURA ----------
fig, ax = plt.subplots(figsize=(13, 7), dpi=170)
ax.set_xlim(0, 13); ax.set_ylim(0, 7); ax.axis('off')
fig.patch.set_facecolor('white')
cols = [('1  FONTES', .2), ('2  INGESTÃO', 2.75), ('3  ARMAZENAMENTO\nE PROCESSAMENTO', 5.15), ('4  MODELO\nANALÍTICO', 7.85), ('5  ENTREGA AO\nUSUÁRIO', 10.45)]
W = [2.3, 2.1, 2.45, 2.35, 2.35]
for (t, x), w in zip(cols, W):
    box(ax, x, 6.15, w, .6, NAVY, r=.08)
    ax.text(x + w / 2, 6.45, t, ha='center', va='center', color='white', fontsize=8.6, fontweight='bold')


def card(x, y, w, h, title, sub, accent=TEAL, fc='white'):
    box(ax, x, y, w, h, fc, BORD, r=.06)
    box(ax, x, y, .09, h, accent, r=.02, z=2)
    ax.text(x + .22, y + h - .2, title, fontsize=8.8, fontweight='bold', color=NAVY, va='top')
    ax.text(x + .22, y + h - .52, sub, fontsize=8, color=GRAY, va='top', linespacing=1.3)


fontes = [('WhatsApp (chatbot)', 'texto, áudio, foto e GPS', PINK), ('Telefone 156', 'atendente registra o pedido', PINK),
          ('App e portal web', 'foto + localização', PINK), ('Agente comunitário', 'registro presencial, offline', PINK),
          ('SP156 dados abertos', 'histórico 2026 (SMIT)', TEAL), ('IBGE Censo 2022', 'população por subprefeitura', TEAL)]
for i, (t, s, c) in enumerate(fontes):
    card(.2, 5.2 - i * .86, 2.3, .74, t, s, c)
ax.text(.2, .1, '■ canais do cidadão   ', color=PINK, fontsize=8)
ax.text(1.75, .1, '■ bases públicas', color=TEAL, fontsize=8)

card(2.75, 4.2, 2.1, 1.75, 'API de chamados', 'recebe os canais em\ntempo real e envia\nconfirmação ao\ncidadão', NAVY)
card(2.75, 2.2, 2.1, 1.75, 'Carga em lote', 'download trimestral\ndos dados abertos\n+ Censo (Python)', NAVY)
card(2.75, .55, 2.1, 1.4, 'Fila offline', 'pedidos do agente\nsincronizam quando\nhá sinal', NAVY)

box(ax, 5.15, .55, 2.45, 5.4, LIGHT, BORD, r=.08)
ax.text(6.375, 5.7, 'Databricks (medalhão)', ha='center', fontsize=9.8, fontweight='bold', color=NAVY)
for j, (t, s, c) in enumerate([('Bronze', 'dados brutos', '#F4E3C9'), ('Prata', 'limpo, padronizado,\nsem duplicados', '#E4E8EF'), ('Ouro', 'KPIs, taxa por mil hab.,\níndice de subnotificação', '#D8F0E8')]):
    yy = 4.45 - j * 1.25
    box(ax, 5.35, yy, 2.05, 1.0, c, BORD, r=.05)
    ax.text(6.375, yy + .68, t, ha='center', fontsize=10, fontweight='bold', color=NAVY)
    ax.text(6.375, yy + .32, s, ha='center', fontsize=7.6, color=TXT, va='center')
box(ax, 5.35, .7, 2.05, .78, 'white', GRAY, r=.04)
ax.plot([5.35, 7.4, 7.4, 5.35, 5.35], [.7, .7, 1.48, 1.48, .7], ls='--', color=GRAY, lw=.8)
ax.text(6.375, 1.2, 'Oracle (dados pessoais)', ha='center', fontsize=7.8, fontweight='bold', color=NAVY)
ax.text(6.375, .9, 'isolado, criptografado (LGPD)', ha='center', fontsize=6.9, color=GRAY)

card(7.85, 4.15, 2.35, 1.8, 'Score de prioridade', 'risco + tempo aberto +\nchamados parecidos +\nEQUIDADE TERRITORIAL\n(novo, vem da análise)', PINK)
card(7.85, 2.25, 2.35, 1.65, 'Previsão de prazo', 'P(resolver em ≤ 7 dias)\npor tipo de serviço', TEAL)
card(7.85, .55, 2.35, 1.45, 'Alerta de território', 'subprefeitura com\npoucos pedidos por\nhabitante', TEAL)

saidas = [('WhatsApp / SMS', 'protocolo, prazo e status', 'Cidadão'), ('Portal de transparência', 'mapa e status, só agregados', 'Cidadão'),
          ('Painel Power BI', 'fila por score e KPIs', 'Gestor público'), ('App da equipe', 'ordem de serviço com rota', 'Equipe de campo')]
for i, (t, s, u) in enumerate(saidas):
    y = 4.95 - i * 1.3
    card(10.45, y, 2.35, 1.1, t, s, NAVY)
    box(ax, 10.67, y + .07, 1.45, .26, LTEAL, r=.05, z=3)
    ax.text(11.395, y + .2, u, ha='center', va='center', fontsize=7.4, color=TEAL, fontweight='bold', zorder=4)

for x0, x1 in [(2.52, 2.73), (4.87, 5.13), (7.62, 7.83), (10.22, 10.43)]:
    for y in [1.5, 3.2, 4.9]:
        ax.annotate('', xy=(x1, y), xytext=(x0, y), arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=1.6))
ax.text(13, .1, 'Fluxo: origem → ingestão → medalhão → modelo → cidadão, gestor e equipe', ha='right', fontsize=8, color=GRAY, style='italic')
plt.savefig('img/arquitetura.png', bbox_inches='tight', facecolor='white'); plt.close()

# ---------- TECNOLOGIAS ----------
techs = [('Coleta', 'WhatsApp Business API, app,\nportal web e telefone 156', 'Receber o pedido pelo canal\nque o cidadão já usa'),
         ('Armazenamento', 'Oracle Database 19c +\nDelta Lake (Databricks)', 'Oracle: dados pessoais\nDelta: histórico analítico'),
         ('Tratamento', 'Python (Pandas, NumPy),\nSpark / PySpark', 'Limpar, padronizar e\njuntar SP156 + Censo'),
         ('Análise', 'SciPy, scikit-learn (fase futura)', 'Testes estatísticos, score\ne previsão de prazo'),
         ('Visualização', 'Power BI, Streamlit, Matplotlib', 'Painel do gestor, portal\ne gráficos de evidência'),
         ('Governança', 'Unity Catalog, acesso\npor perfil', 'LGPD: quem vê o quê,\ntrilha de auditoria')]
fig, ax = plt.subplots(figsize=(9, 5.3), dpi=170)
ax.set_xlim(0, 9); ax.set_ylim(0, 5.3); ax.axis('off')
box(ax, 0, 4.7, 9, .55, NAVY, r=.05)
for x, t in [(.15, 'ETAPA'), (1.95, 'TECNOLOGIA'), (5.6, 'PARA QUE SERVE')]:
    ax.text(x, 4.97, t, color='white', fontsize=10, fontweight='bold', va='center')
for i, (e, t, p) in enumerate(techs):
    y = 3.95 - i * .76
    box(ax, 0, y, 9, .68, LIGHT if i % 2 == 0 else 'white', BORD, r=.04)
    box(ax, .12, y + .17, 1.6, .34, TEAL, r=.08)
    ax.text(.92, y + .34, e, ha='center', va='center', color='white', fontsize=9, fontweight='bold')
    ax.text(1.95, y + .34, t, va='center', fontsize=8.4, color=NAVY, fontweight='bold', linespacing=1.2)
    ax.text(5.6, y + .34, p, va='center', fontsize=8.2, color=TXT, linespacing=1.2)
plt.savefig('img/tecnologias.png', bbox_inches='tight', facecolor='white'); plt.close()

# ---------- PROTOTIPO (3 telas low-fi) ----------
fig, ax = plt.subplots(figsize=(13, 6.6), dpi=170)
ax.set_xlim(0, 13); ax.set_ylim(0, 6.6); ax.axis('off')


def phone(x, title, color):
    box(ax, x, .2, 3.1, 6.2, NAVY, r=.25)
    box(ax, x + .15, .45, 2.8, 5.7, 'white', r=.12)
    box(ax, x + .15, 5.55, 2.8, .6, color, r=.08)
    ax.text(x + 1.55, 5.85, title, ha='center', va='center', color='white', fontsize=10, fontweight='bold')


# Tela 1: WhatsApp
phone(.2, 'UrbanIQ no WhatsApp', '#128C7E')
msgs = [(False, 'Olá! Qual o problema?\n1 Buraco  2 Entulho\n3 Árvore  4 Outro\n🔊 Prefere ouvir? Envie "áudio"'),
        (True, '1'), (False, 'Envie uma foto e a\nlocalização (ou o\nendereço por áudio).'),
        (True, '📷 📍'),
        (False, 'Protocolo UIQ-48213\nPrazo provável: até\n7 dias (60% dos casos).\nAviso aqui a cada etapa.')]
y = 5.25
for me, t in msgs:
    n = t.count('\n') + 1
    h = .2 + n * .2
    w = 1.25 if me else 2.2
    xx = .45 + (2.6 - w - .02 if me else 0)
    box(ax, xx, y - h, w, h, '#DCF8C6' if me else LIGHT, BORD, r=.06)
    ax.text(xx + .1, y - .1, t.replace('🔊', '»').replace('📷', '[foto]').replace('📍', '[local]'), va='top', fontsize=7.3, color=TXT, linespacing=1.25)
    y -= h + .12
ax.text(1.75, .05, '① WhatsApp: sem app, com áudio', ha='center', fontsize=8.5, color=NAVY, fontweight='bold')

# Tela 2: Portal de transparência
phone(3.6, 'Acompanhe seu chamado', TEAL)
ax.text(3.9, 5.25, 'UIQ-48213 · Buraco na via', fontsize=8.6, fontweight='bold', color=NAVY)
ax.text(3.9, 5.0, 'Cidade Tiradentes', fontsize=7.6, color=GRAY)
etapas = [('Aberto', '12/11', True), ('Em análise', '13/11', True), ('Em atendimento', 'equipe a caminho', True), ('Resolvido', 'previsto até 19/11', False), ('Avalie o serviço', '★★★★★', False)]
for i, (e, d, ok) in enumerate(etapas):
    yy = 4.55 - i * .62
    ax.add_patch(Circle((4.05, yy), .1, fc=TEAL if ok else 'white', ec=TEAL, lw=1.5, zorder=3))
    if i < 4:
        ax.plot([4.05, 4.05], [yy - .1, yy - .52], color=TEAL if ok else BORD, lw=2)
    ax.text(4.3, yy + .04, e, fontsize=8.2, color=NAVY, fontweight='bold' if ok else 'normal', va='center')
    ax.text(4.3, yy - .2, d, fontsize=7, color=GRAY, va='center')
box(ax, 3.85, .6, 2.6, 1.05, LTEAL, r=.06)
ax.text(3.95, 1.45, 'No seu bairro (30 dias)', fontsize=7.6, color=TEAL, fontweight='bold')
ax.text(3.95, 1.15, '41 resolvidos · mediana 2 dias', fontsize=7.4, color=TXT)
ax.text(3.95, .85, 'Fonte acessível · alto contraste', fontsize=7, color=GRAY)
ax.text(5.15, .05, '② Portal: etapa, prazo, avaliação', ha='center', fontsize=8.5, color=NAVY, fontweight='bold')

# Tela 3: Painel do gestor (desktop)
X = 7.0
box(ax, X, .45, 5.85, 5.95, NAVY, r=.12)
box(ax, X + .12, .6, 5.61, 5.4, 'white', r=.06)
ax.text(X + .3, 6.15, 'Fila priorizada · Subprefeitura Cidade Tiradentes', color='white', fontsize=9.5, fontweight='bold', va='center')
for i, (k, v, c) in enumerate([('Abertos', '312', NAVY), ('Urgentes (≥80)', '17', PINK), ('Pedidos/mil hab.', '12,6', TEAL), ('Índice subnotif.', '1,00', PINK)]):
    xx = X + .25 + i * 1.37
    box(ax, xx, 5.0, 1.27, .82, LIGHT, BORD, r=.05)
    ax.text(xx + .635, 5.5, v, ha='center', fontsize=13, fontweight='bold', color=c)
    ax.text(xx + .635, 5.15, k, ha='center', fontsize=6.8, color=GRAY)
hdr = ['Protocolo', 'Serviço', 'Dias', 'Score', 'Equidade']
xs = [X + .3, X + 1.4, X + 3.05, X + 3.75, X + 4.6]
box(ax, X + .25, 4.45, 5.35, .35, NAVY, r=.03)
for xx, h in zip(xs, hdr):
    ax.text(xx, 4.62, h, color='white', fontsize=7.8, fontweight='bold', va='center')
rows = [('UIQ-48177', 'Árvore c/ risco', '9', 80), ('UIQ-48213', 'Buraco na via', '6', 78), ('UIQ-48301', 'Boca de lobo', '3', 71), ('UIQ-48290', 'Entulho', '2', 58), ('UIQ-48322', 'Poste apagado', '1', 46)]
for i, (p, s, d, sc) in enumerate(rows):
    yy = 4.05 - i * .42
    box(ax, X + .25, yy - .16, 5.35, .36, LIGHT if i % 2 == 0 else 'white', r=.02)
    for xx, t in zip(xs[:3], [p, s, d]):
        ax.text(xx, yy, t, fontsize=7.6, color=TXT, va='center')
    col = PINK if sc >= 80 else ('#F29F05' if sc >= 60 else TEAL)
    box(ax, xs[3] - .05, yy - .12, .62, .26, col, r=.05)
    ax.text(xs[3] + .26, yy, str(sc), ha='center', va='center', color='white', fontsize=7.8, fontweight='bold')
    ax.text(xs[4], yy, '+10', fontsize=7.6, color=TEAL, va='center', fontweight='bold')
box(ax, X + .25, .75, 5.35, 1.15, LTEAL, r=.05)
ax.text(X + .4, 1.65, 'Por que este score? (UIQ-48213)', fontsize=7.8, color=TEAL, fontweight='bold')
ax.text(X + .4, 1.35, 'Risco 45 (via de ônibus) + tempo 3 (6 dias) + parecidos 20 + equidade 10 = 78', fontsize=6.6, color=TXT)
ax.text(X + .4, 1.05, 'Regra explicável: o gestor vê cada parcela e pode ajustar com justificativa registrada.', fontsize=6.6, color=TXT)
ax.text(X + 2.93, .05, '③ Painel do gestor: fila ordenada pelo score com equidade', ha='center', fontsize=8.5, color=NAVY, fontweight='bold')
plt.savefig('img/prototipo.png', bbox_inches='tight', facecolor='white'); plt.close()
print('ok')
