import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, FancyBboxPatch, Arc, Wedge
import os

NAVY, TEAL, PINK, WHITE, GRAY = '#1E2A4A', '#12A594', '#ED185C', '#FFFFFF', '#6B7488'
os.makedirs('logos', exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'


def pin(ax, cx, cy, r, color, z=2):
    ax.add_patch(Circle((cx, cy), r, fc=color, ec='none', zorder=z))
    ax.add_patch(Polygon([(cx - r * .86, cy - r * .5), (cx + r * .86, cy - r * .5), (cx, cy - r * 2.05)], fc=color, ec='none', zorder=z))


def icone1(ax, cx, cy, r, pin_c=TEAL, bal_c=WHITE, dot_c=NAVY):
    """Ideia 1: pin cujo interior é um balão de fala."""
    pin(ax, cx, cy, r, pin_c)
    w, h = r * 1.3, r * .86
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2 + r * .05), w, h, boxstyle=f'round,pad=0,rounding_size={r * .22}', fc=bal_c, ec='none', zorder=3))
    ax.add_patch(Polygon([(cx - w * .18, cy - h / 2 + r * .08), (cx - w * .02, cy - h / 2 + r * .08), (cx - w * .3, cy - h / 2 - r * .2)], fc=bal_c, ec='none', zorder=3))
    for k, c in zip((-1, 0, 1), (dot_c, PINK, dot_c)):
        ax.add_patch(Circle((cx + k * w * .27, cy + r * .05), r * .09, fc=c, ec='none', zorder=4))


def icone2(ax, cx, cy, r, pin_c=TEAL, hole=WHITE, wave_c=PINK):
    """Ideia 2: pin com ondas de som saindo dele."""
    pin(ax, cx, cy, r, pin_c)
    ax.add_patch(Circle((cx, cy), r * .4, fc=hole, ec='none', zorder=3))
    for k, a in enumerate((1.0, .75, .5)):
        ax.add_patch(Arc((cx + r * .15, cy), r * (2.6 + k * .9), r * (2.6 + k * .9), theta1=-38, theta2=38,
                         lw=r * (11 - k * 1.5), color=wave_c, alpha=a, capstyle='round', zorder=1))


def wordmark(ax, x, y, size, c_urban=NAVY, c_iq=TEAL, tag_c=GRAY, tag=True):
    t = ax.text(x, y, 'Urban', fontsize=size, fontweight='bold', color=c_urban, va='center', ha='left')
    ax.figure.canvas.draw()
    bb = t.get_window_extent().transformed(ax.transData.inverted())
    ax.text(bb.x1, y, 'IQ', fontsize=size, fontweight='bold', color=c_iq, va='center', ha='left')
    if tag:
        ax.text(x + .005, y - .25, 'zeladoria que escuta todo território', fontsize=size * .3, color=tag_c, va='center', ha='left')


def horizontal(icone, nome, dark=False):
    fig, ax = plt.subplots(figsize=(7, 2.4), dpi=220)
    ax.set_xlim(0, 2.9); ax.set_ylim(0, 1); ax.axis('off')
    bg = NAVY if dark else WHITE
    fig.patch.set_facecolor(bg)
    if icone == 1:
        icone1(ax, .42, .6, .2, TEAL, WHITE, NAVY)
    else:
        icone2(ax, .38, .6, .2, TEAL, WHITE if not dark else NAVY, PINK)
    wordmark(ax, .82 if icone == 1 else 1.0, .6, 46, WHITE if dark else NAVY, TEAL, '#C9D3E6' if dark else GRAY)
    plt.savefig(f'logos/{nome}.png', facecolor=bg, bbox_inches='tight', pad_inches=.15); plt.close()


def app(icone, nome):
    fig, ax = plt.subplots(figsize=(3, 3), dpi=220)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off'); fig.patch.set_alpha(0)
    ax.add_patch(FancyBboxPatch((.04, .04), .92, .92, boxstyle='round,pad=0,rounding_size=.2', fc=NAVY, ec='none'))
    if icone == 1:
        icone1(ax, .5, .66, .17, TEAL, WHITE, NAVY)
    else:
        icone2(ax, .4, .66, .16, TEAL, NAVY, PINK)
    ax.text(.5, .14, 'UrbanIQ', ha='center', va='center', fontsize=17, fontweight='bold', color=WHITE)
    plt.savefig(f'logos/{nome}.png', transparent=True, bbox_inches='tight', pad_inches=0); plt.close()


horizontal(1, 'ideia1_horizontal_claro'); horizontal(1, 'ideia1_horizontal_escuro', True); app(1, 'ideia1_icone_app')
horizontal(2, 'ideia2_horizontal_claro'); horizontal(2, 'ideia2_horizontal_escuro', True); app(2, 'ideia2_icone_app')

# folha de comparação
from PIL import Image, ImageDraw, ImageFont
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
W = 1900
sheet = Image.new('RGB', (W, 1250), '#F3F6FA'); d = ImageDraw.Draw(sheet)
d.text((60, 30), 'UrbanIQ | propostas de logotipo', font=F(46), fill=NAVY)
for row, (ideia, titulo) in enumerate([(1, 'Ideia 1: pin + balão de fala (lugar + voz)'), (2, 'Ideia 2: pin com ondas de som ("toda rua seja ouvida")')]):
    y0 = 120 + row * 560
    d.text((60, y0), titulo, font=F(32), fill=TEAL)
    x = 60
    for v in ('horizontal_claro', 'horizontal_escuro'):
        im = Image.open(f'logos/ideia{ideia}_{v}.png').convert('RGBA'); im.thumbnail((600, 230))
        sheet.paste(im, (x, y0 + 70), im); x += im.width + 40
    ic = Image.open(f'logos/ideia{ideia}_icone_app.png').convert('RGBA'); ic.thumbnail((300, 300))
    sheet.paste(ic, (x + 20, y0 + 50), ic)
    for k, s in enumerate((96, 64, 40)):
        t = ic.copy(); t.thumbnail((s, s)); sheet.paste(t, (x + 20 + k * 110, y0 + 380), t)
    d.text((x + 20, y0 + 490), 'tamanhos pequenos', font=F(18), fill=GRAY)
sheet.save('logos/comparacao_logos.png')
print('ok')
