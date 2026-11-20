import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Arc
from PIL import Image
NAVY, TEAL, PINK = '#1E2A4A', '#12A594', '#ED185C'

def render(urban_c, tag_c, nome):
    def base(mask_only=False):
        fig, ax = plt.subplots(figsize=(7, 2.4), dpi=220)
        ax.set_xlim(0, 2.9); ax.set_ylim(0, 1); ax.axis('off'); fig.patch.set_alpha(0); ax.patch.set_alpha(0)
        cx, cy, r = .38, .6, .2
        if mask_only:
            ax.add_patch(Circle((cx, cy), r * .4, fc='black', ec='none'))
        else:
            ax.add_patch(Circle((cx, cy), r, fc=TEAL, ec='none'))
            ax.add_patch(Polygon([(cx - r*.86, cy - r*.5), (cx + r*.86, cy - r*.5), (cx, cy - r*2.05)], fc=TEAL, ec='none'))
            for k, a in enumerate((1.0, .75, .5)):
                d = r * (2.6 + k * .9)
                ax.add_patch(Arc((cx + r*.15, cy), d, d, theta1=-38, theta2=38, lw=r*(11-k*1.5), color=PINK, alpha=a, capstyle='round'))
            t = ax.text(1.0, .6, 'Urban', fontsize=46, fontweight='bold', color=urban_c, va='center')
            fig.canvas.draw(); bb = t.get_window_extent().transformed(ax.transData.inverted())
            ax.text(bb.x1, .6, 'IQ', fontsize=46, fontweight='bold', color=TEAL, va='center')
            ax.text(1.005, .35, 'zeladoria que escuta todo território', fontsize=46*.3, color=tag_c, va='center')
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba()).copy(); plt.close(fig); return img
    img, mask = base(), base(True)
    a = img[..., 3].astype(float) * (1 - mask[..., 3].astype(float) / 255)
    img[..., 3] = a.astype(np.uint8)
    im = Image.fromarray(img); im = im.crop(im.getbbox())
    pad = 30; out = Image.new('RGBA', (im.width + 2*pad, im.height + 2*pad), (0, 0, 0, 0)); out.paste(im, (pad, pad))
    out.save(f'logos/{nome}.png'); return out

claro = render(NAVY, '#6B7488', 'logo-urbaniq-transparente-claro')
escuro = render('#FFFFFF', '#C9D3E6', 'logo-urbaniq-transparente-escuro')
# prévia: como fica no GitHub claro e escuro
W = max(claro.width, escuro.width) + 80
prev = Image.new('RGB', (W, claro.height + escuro.height + 120), '#FFFFFF')
dark = Image.new('RGB', (W, escuro.height + 60), '#0D1117'); prev.paste(dark, (0, claro.height + 60))
prev.paste(claro, (40, 30), claro); prev.paste(escuro, (40, claro.height + 90), escuro)
prev.save('logos/previa_github_claro_escuro.png'); print(claro.size, escuro.size)
