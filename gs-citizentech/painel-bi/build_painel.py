"""Gera a página do painel (formato PBIR) do UrbanIQ - GS 2026.2."""
import json, os, sys

BASE = sys.argv[1]  # .../definition/pages/<page>
REUSE = sys.argv[2] if len(sys.argv) > 2 else None  # pasta de visual já existente para reaproveitar
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
NAVY, TEAL, PINK, TXT, GRAY = '#1E2A4A', '#12A594', '#ED185C', '#3A4459', '#6B7488'
ANEL = {'Central': '#1F77B4', 'Intermediário': '#FF7F0E', 'Periférico': '#2CA02C'}
CANAL = {'Telefone 156': '#D62728', 'WhatsApp': '#9467BD', 'Aplicativo': '#FF7F0E', 'Portal web': '#1F77B4', 'Outros': '#B0B7C3'}

lit = lambda v: {"expr": {"Literal": {"Value": v}}}
s = lambda t: lit("'" + t.replace("'", "''") + "'")
col = lambda e, p: {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}
mea = lambda p, e='pbi_chamados': {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}
agg = lambda e, p, f: {"Aggregation": {"Expression": col(e, p), "Function": f}}  # 0 soma, 1 média


def proj(field, ref, native):
    return {"field": field, "queryRef": ref, "nativeQueryRef": native}


C = lambda e, p: proj(col(e, p), f"{e}.{p}", p)
M = lambda p, e='pbi_chamados': proj(mea(p, e), f"{e}.{p}", p)
A = lambda e, p, f: proj(agg(e, p, f), f"{'Sum' if f == 0 else 'Avg'}({e}.{p})", p)


def title(text, size=13):
    return {"title": [{"properties": {"show": lit("true"), "text": s(text), "fontColor": {"solid": {"color": s(NAVY)}},
                                      "fontSize": lit(f"{size}D"), "bold": lit("true")}}],
            "background": [{"properties": {"show": lit("true"), "color": {"solid": {"color": s('#FFFFFF')}}}}],
            "border": [{"properties": {"show": lit("true"), "color": {"solid": {"color": s('#D9E1EC')}}, "radius": lit("8D")}}],
            "dropShadow": [{"properties": {"show": lit("false")}}],
            "subTitle": [{"properties": {"show": lit("false")}}]}


def colors(entity, prop, mapping):
    return [{"properties": {"fill": {"solid": {"color": s(c)}}},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": col(entity, prop),
                                                                "Right": {"Literal": {"Value": "'" + k + "'"}}}}}]}}
            for k, c in mapping.items()]


visuals = []
z = [0]


def add(name, x, y, w, h, visual, vco=None):
    z[0] += 1
    v = {"$schema": SCHEMA, "name": name,
         "position": {"x": x, "y": y, "z": z[0] * 1000, "height": h, "width": w, "tabOrder": z[0] * 1000},
         "visual": visual}
    if vco:
        v["visual"]["visualContainerObjects"] = vco
    v["visual"]["drillFilterOtherVisuals"] = True
    visuals.append(v)


def textbox(name, x, y, w, h, paragraphs, bg=None):
    vis = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]}}
    vco = {"background": [{"properties": {"show": lit("true" if bg else "false"), **({"color": {"solid": {"color": s(bg)}}} if bg else {})}}]}
    add(name, x, y, w, h, vis, vco)


def run(t, size=11, bold=False, color=TXT):
    st = {"fontSize": f"{size}pt", "color": color}
    if bold:
        st["fontWeight"] = "bold"
    return {"value": t, "textStyle": st}


# ---------- Cabeçalho ----------
textbox('v01titulo', 20, 12, 1100, 80, [
    {"textRuns": [run('UrbanIQ | Zeladoria urbana em São Paulo: quem chega até a Prefeitura?', 22, True, NAVY)]},
    {"textRuns": [run('Chamados de zeladoria do SP156 (abr a set/2026) cruzados com a população do Censo 2022, por subprefeitura e anel territorial.', 11, False, GRAY)]}])


def slicer(name, x, y, w, h, field, label, mode='Dropdown'):
    vis = {"visualType": "slicer",
           "query": {"queryState": {"Values": {"projections": [field]}}},
           "objects": {"data": [{"properties": {"mode": s(mode)}}],
                       "header": [{"properties": {"show": lit("true"), "text": s(label), "fontColor": {"solid": {"color": s(NAVY)}}, "bold": lit("true")}}],
                       "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true")}}]}}
    add(name, x, y, w, h, vis, {"background": [{"properties": {"show": lit("true"), "color": {"solid": {"color": s('#FFFFFF')}}}}],
                                 "border": [{"properties": {"show": lit("true"), "color": {"solid": {"color": s('#D9E1EC')}}, "radius": lit("8D")}}]})


slicer('v02f_anel', 1140, 10, 250, 82, C('pbi_subprefeituras', 'anel'), 'Anel territorial')
slicer('v03f_mes', 1400, 10, 160, 82, C('Calendario', 'Mes'), 'Mês')
slicer('v04f_serv', 1570, 10, 165, 82, C('pbi_chamados', 'servico'), 'Serviço')
slicer('v05f_sub', 1745, 10, 155, 82, C('pbi_subprefeituras', 'subprefeitura'), 'Subprefeitura')

# ---------- KPIs ----------
kpis = [('Total de Chamados', 'Chamados de zeladoria', NAVY), ('Chamados por Mil Hab', 'Chamados por mil habitantes', TEAL),
        ('Mediana de Dias', 'Mediana de dias até finalizar', NAVY), ('% Resolvido em 7 Dias', 'Resolvidos em até 7 dias', TEAL),
        ('% Telefone ou WhatsApp', 'Pedidos por telefone ou WhatsApp', PINK)]
for i, (m, label, cor) in enumerate(kpis):
    vis = {"visualType": "card", "query": {"queryState": {"Values": {"projections": [M(m)]}}},
           "objects": {"labels": [{"properties": {"color": {"solid": {"color": s(cor)}}, "fontSize": lit("30D")}}],
                       "categoryLabels": [{"properties": {"show": lit("false")}}]}}
    vco = title(label, 11)
    add(f'v1{i}kpi', 20 + i * 378, 105, 368, 125, vis, vco)

# ---------- Visual A: evolução temporal ----------
vis = {"visualType": "lineChart",
       "query": {"queryState": {"Category": {"projections": [C('Calendario', 'Mes')]},
                                "Y": {"projections": [M('Total de Chamados')]},
                                "Series": {"projections": [C('pbi_subprefeituras', 'anel')]}},
                 "sortDefinition": {"sort": [{"field": col('Calendario', 'Mes'), "direction": "Ascending"}], "isDefaultSort": True}},
       "objects": {"dataPoint": colors('pbi_subprefeituras', 'anel', ANEL),
                   "legend": [{"properties": {"show": lit("true"), "position": s('Top')}}],
                   "labels": [{"properties": {"show": lit("false")}}],
                   "categoryAxis": [{"properties": {"showAxisTitle": lit("true"), "titleText": s('Mês de abertura')}}],
                   "valueAxis": [{"properties": {"showAxisTitle": lit("true"), "titleText": s('Chamados')}}],
                   "lineStyles": [{"properties": {"strokeWidth": lit("3L"), "showMarker": lit("true")}}]}}
add('v20linha', 20, 245, 935, 395, vis, title('A. Evolução mensal: volumes parecidos nos três anéis (escolhi linha para mostrar tendência no tempo)'))

# ---------- Visual C: mapa (distribuição territorial) ----------
vis = {"visualType": "azureMap",
       "query": {"queryState": {"Category": {"projections": [C('pbi_subprefeituras', 'subprefeitura')]},
                                "Series": {"projections": [C('pbi_subprefeituras', 'anel')]},
                                "Y": {"projections": [A('pbi_subprefeituras', 'lat_centro', 1)]},
                                "X": {"projections": [A('pbi_subprefeituras', 'lon_centro', 1)]},
                                "Size": {"projections": [M('Chamados por Mil Hab')]},
                                "Tooltips": {"projections": [A('pbi_subprefeituras', 'pop_2022', 0), M('Mediana de Dias'), M('% Telefone ou WhatsApp')]}}},
       "objects": {"dataPoint": colors('pbi_subprefeituras', 'anel', ANEL),
                   "legend": [{"properties": {"show": lit("true"), "position": s('Top')}}]}}
add('v30disp', 965, 245, 935, 395, vis, title('C. Mapa: tamanho da bolha = chamados por mil hab. As bordas da cidade pedem menos'))

# ---------- Visual B: ranking ----------
vis = {"visualType": "barChart",
       "query": {"queryState": {"Category": {"projections": [C('pbi_subprefeituras', 'subprefeitura')]},
                                "Y": {"projections": [M('Chamados por Mil Hab')]},
                                "Series": {"projections": [C('pbi_subprefeituras', 'anel')]}},
                 "sortDefinition": {"sort": [{"field": mea('Chamados por Mil Hab'), "direction": "Ascending"}], "isDefaultSort": False}},
       "objects": {"dataPoint": colors('pbi_subprefeituras', 'anel', ANEL),
                   "legend": [{"properties": {"show": lit("true"), "position": s('Top')}}],
                   "labels": [{"properties": {"show": lit("true"), "fontSize": lit("8D")}}],
                   "categoryAxis": [{"properties": {"fontSize": lit("8D"), "showAxisTitle": lit("false")}}],
                   "valueAxis": [{"properties": {"show": lit("false")}}]}}
add('v40rank', 20, 655, 620, 410, vis, title('B. Ranking: subprefeituras que menos pedem por habitante'))

# ---------- Visual D: canal por anel ----------
vis = {"visualType": "hundredPercentStackedBarChart",
       "query": {"queryState": {"Category": {"projections": [C('pbi_subprefeituras', 'anel')]},
                                "Y": {"projections": [M('Total de Chamados')]},
                                "Series": {"projections": [C('pbi_chamados', 'canal_nome')]}},
                 "sortDefinition": {"sort": [{"field": col('pbi_subprefeituras', 'anel'), "direction": "Ascending"}], "isDefaultSort": True}},
       "objects": {"dataPoint": colors('pbi_chamados', 'canal_nome', CANAL),
                   "legend": [{"properties": {"show": lit("true"), "position": s('Bottom')}}],
                   "labels": [{"properties": {"show": lit("true"), "fontSize": lit("9D")}}],
                   "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
                   "valueAxis": [{"properties": {"showAxisTitle": lit("false")}}]}}
add('v50canal', 650, 655, 640, 330, vis, title('D. Canal usado por anel: a periferia usa mais telefone e WhatsApp'))

# ---------- Insights ----------
textbox('v60insights', 1300, 655, 600, 410, [
    {"textRuns": [run('3 principais insights', 15, True, NAVY)]},
    {"textRuns": [run(' ', 6)]},
    {"textRuns": [run('1. O prazo é igual para todos. ', 11.5, True, TEAL), run('A mediana é de 2 dias e cerca de 75% dos chamados são resolvidos em até 7 dias, no centro e na periferia.', 11.5)]},
    {"textRuns": [run(' ', 6)]},
    {"textRuns": [run('2. A periferia pede 22% menos por habitante. ', 11.5, True, PINK), run('São 18,6 contra 23,9 pedidos por mil habitantes. Cidade Tiradentes registra menos da metade do que Jabaquara: o problema existe, mas não vira chamado.', 11.5)]},
    {"textRuns": [run(' ', 6)]},
    {"textRuns": [run('3. Um canal só digital excluiria quem já pede menos. ', 11.5, True, NAVY), run('Na periferia, 34% dos pedidos chegam por telefone ou WhatsApp.', 11.5)]},
    {"textRuns": [run(' ', 6)]},
    {"textRuns": [run('Conexão com a solução: ', 11.5, True, TEAL), run('o UrbanIQ é omnichannel (WhatsApp, áudio, 156, agente comunitário) e soma um bônus de equidade ao score de prioridade.', 11.5)]}],
    bg='#E3F5F2')

textbox('v70fonte', 650, 995, 640, 70, [
    {"textRuns": [run('Fonte: SP156/SMIT, Prefeitura de São Paulo (abr a set/2026, extraído em 19/10/2026); IBGE, Censo 2022. Tratamento em Python (Parte 3). Anéis = tercis da distância até o Marco Zero. Cores seguras para daltonismo.', 8.5, False, GRAY)]}])

# ---------- grava ----------
os.makedirs(os.path.join(BASE, 'visuals'), exist_ok=True)
for i, v in enumerate(visuals):
    name = v['name']
    if REUSE and i == 0:
        name = REUSE; v['name'] = REUSE
    d = os.path.join(BASE, 'visuals', name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'visual.json'), 'w', encoding='utf-8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)

page = json.load(open(os.path.join(BASE, 'page.json'), encoding='utf-8'))
page['displayName'] = 'Painel UrbanIQ'
page['objects'] = {"background": [{"properties": {"color": {"solid": {"color": s('#F3F6FA')}}, "transparency": lit("0D")}}]}
json.dump(page, open(os.path.join(BASE, 'page.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(visuals), 'visuais gravados')
