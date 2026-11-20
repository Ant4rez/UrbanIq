import re, subprocess

BLOCOS = {
1: "Olá, eu sou o Thiago Fiel de Oliveira, da turma 1TSCOB, equipe DataGuy. Este é o UrbanIQ, uma CitizenTech de zeladoria urbana. A ideia é simples: o problema da rua precisa chegar até a Prefeitura, venha de onde vier.",
2: "Eu comecei com uma hipótese: na periferia de São Paulo, a Prefeitura demora mais para resolver buraco, entulho ou árvore caída. Para testar, analisei em Python 245 mil pedidos reais do SP156, de abril a setembro de 2026, cruzados com o Censo 2022. E os dados me surpreenderam. O tempo de atendimento é igual: mediana de 2 dias no centro e na periferia. O problema está em outro lugar. A periferia registra 22% menos pedidos por habitante. Repare no mapa: as bolhas roxas, nas bordas da cidade, são os territórios que menos pedem. Cidade Tiradentes faz menos da metade dos pedidos do Jabaquara. Não é que lá tenha menos buraco: o problema existe, mas não vira chamado. É o caso da Dona Cida, 64 anos, que só usa WhatsApp e áudio, vê o entulho na esquina há semanas e acha que não adianta reclamar.",
3: "Por isso o UrbanIQ ataca a porta de entrada. Ele é omnichannel: o cidadão abre o pedido pelo WhatsApp, com menu numérico ou áudio, pelo telefone 156, pelo aplicativo, ou com um agente comunitário que registra até sem internet. Depois, cada pedido recebe um score de prioridade explicável: risco, tempo em aberto, reiterações e um bônus de equidade para os territórios que pedem pouco, porque ali cada pedido provavelmente representa vários problemas que ninguém relatou. E o cidadão recebe um prazo realista já na abertura, calculado com a probabilidade de resolução em 7 dias para aquele tipo de serviço. Quem ganha: moradores da periferia, gestores das subprefeituras e equipes de campo. Quem faz funcionar: Prefeitura, IBGE, associações de bairro e o canal WhatsApp.",
4: "Aqui estão as três telas do protótipo. No WhatsApp, a Dona Cida manda foto e local e recebe o protocolo com o prazo provável. No portal, ela acompanha cada etapa e avalia o serviço. E o gestor vê a fila ordenada pelo score, com cada parcela explicada, inclusive o bônus de equidade.",
5: "No painel do Power BI, com filtros por território, mês e serviço, e com o mapa interativo, ficam claros os três insights. Primeiro: o prazo é igual em toda a cidade. Segundo: a periferia pede 22% menos por habitante. Terceiro: um terço dos pedidos da periferia chega por telefone ou WhatsApp. Ou seja, uma solução só digital deixaria de fora justamente quem já pede menos.",
6: "A arquitetura usa o que eu já trabalhei no curso: os canais e as bases públicas entram por API e por carga em lote, passam pelo medalhão no Databricks, e os dados pessoais ficam isolados no Oracle, seguindo a LGPD. A análise usa só dados agregados, e o próprio score corrige o viés de priorizar quem mais reclama.",
7: "A meta é subir os pedidos por habitante na periferia de 18,6 para 22 por mil, sem piorar os 74% resolvidos em até uma semana. Isso conecta o UrbanIQ aos ODS 10, 11 e 16. O UrbanIQ não conserta a rua, mas garante que toda rua seja ouvida. Obrigado!",
}
G, INTRO, MAXC = 0.35, 1.5, 84


def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)


def gaps(f):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-i', f, '-af', 'silencedetect=n=-22dB:d=0.18', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    return [(a + b) / 2 for a, b in zip(st, en)]


def chunks(text):
    """Quebra em legendas de até MAXC caracteres, preferindo fim de frase e vírgulas."""
    frases = re.split(r'(?<=[.!?:])\s+', text)
    out = []
    for f in frases:
        while len(f) > MAXC:
            corte = max(f.rfind(', ', 0, MAXC), f.rfind(' e ', 0, MAXC), f.rfind(' ', 0, MAXC) if f.rfind(', ', 0, MAXC) < 30 else -1)
            if corte < 25:
                corte = f.rfind(' ', 0, MAXC)
            out.append(f[:corte + 1].strip()); f = f[corte + 1:].strip()
        if f:
            out.append(f)
    return out


def quebra_linha(t, lim=44):
    if len(t) <= lim:
        return t
    meio = len(t) // 2
    esq, dir_ = t.rfind(' ', 0, meio + 6), t.find(' ', meio - 6)
    pos = esq if (meio - esq) <= (dir_ - meio if dir_ > 0 else 99) else dir_
    return t[:pos] + '\\N' + t[pos + 1:]


def ts(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{r:05.2f}"


def ts_srt(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60); ms = int(round((r - int(r)) * 1000))
    return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{ms:03d}"


subs = []
t0 = INTRO
for i in range(1, 8):
    f = f'a{i}.wav'; d = dur(f); gp = gaps(f)
    cs = chunks(BLOCOS[i]); tot = sum(len(c) for c in cs)
    acc, ini = 0, 0.0
    for k, c in enumerate(cs):
        acc += len(c)
        fim = d if k == len(cs) - 1 else d * acc / tot
        if k < len(cs) - 1 and gp:
            perto = min(gp, key=lambda g: abs(g - fim))
            if abs(perto - fim) < 1.2 and perto > ini + 0.8:
                fim = perto
        subs.append((t0 + ini, t0 + fim, c))
        ini = fim
    t0 += d + G

ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,46,&H00FFFFFF,&H00FFFFFF,&H184A2A1E,&H184A2A1E,0,0,0,0,100,100,0,0,3,14,0,2,120,120,38,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
srt = []
for n, (a, b, t) in enumerate(subs, 1):
    ass += f"Dialogue: 0,{ts(a)},{ts(b - 0.05)},Default,,0,0,0,,{quebra_linha(t)}\n"
    srt.append(f"{n}\n{ts_srt(a)} --> {ts_srt(b - 0.05)}\n{quebra_linha(t).replace(chr(92) + 'N', chr(10))}\n")
open('legendas.ass', 'w', encoding='utf-8').write(ass)
open('GS_1TSCOB_Pitch_UrbanIQ_DataGuy.srt', 'w', encoding='utf-8').write('\n'.join(srt))
print(len(subs), 'legendas; última termina em', round(subs[-1][1], 1), 's')
for a, b, t in subs[:6]:
    print(round(a, 1), round(b, 1), t)
