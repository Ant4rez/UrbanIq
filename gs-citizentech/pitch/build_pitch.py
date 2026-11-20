import copy, re, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PAINEL = sys.argv[1] if len(sys.argv) > 1 else None
LINK = sys.argv[2] if len(sys.argv) > 2 else 'https://youtu.be/LINK-DO-VIDEO'

p = Presentation('template.pptx')
S = lambda n: p.slides[n - 1]


def shp(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def fill(sh, paras, size=None, color=None):
    """Reescreve o texto mantendo o estilo do 1º run do template. **x** = negrito."""
    tf = sh.text_frame
    p0 = tf.paragraphs[0]
    pPr = copy.deepcopy(p0._p.pPr) if p0._p.pPr is not None else None
    r0 = p0.runs[0]._r
    rPr = copy.deepcopy(r0.rPr) if r0.rPr is not None else None
    for para in list(tf.paragraphs)[1:]:
        para._p.getparent().remove(para._p)
    for r in list(p0._p):
        if r.tag.endswith('}r') or r.tag.endswith('}br') or r.tag.endswith('}fld'):
            p0._p.remove(r)
    for i, txt in enumerate(paras):
        para = p0 if i == 0 else tf.add_paragraph()
        if i > 0 and pPr is not None:
            if para._p.pPr is not None:
                para._p.remove(para._p.pPr)
            para._p.insert(0, copy.deepcopy(pPr))
        for k, part in enumerate(re.split(r'\*\*', txt)):
            if not part:
                continue
            run = para.add_run()
            if rPr is not None:
                new = copy.deepcopy(rPr)
                run._r.insert(0, new)
            run.text = part
            run.font.bold = (k % 2 == 1)
            if size:
                run.font.size = Pt(size)
            if color:
                run.font.color.rgb = RGBColor.from_string(color)


def delete(slide, *names):
    for n in names:
        el = shp(slide, n)._element
        el.getparent().remove(el)


def picture_in(slide, path, x, y, w, h):
    from PIL import Image
    iw, ih = Image.open(path).size
    r = min(w / iw, h / ih)
    pw, ph = iw * r, ih * r
    return slide.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def note(slide, text, x=0.5, y=4.95, w=8.6, h=0.25, size=7.5):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    r = tb.text_frame.paragraphs[0].add_run()
    r.text = text; r.font.size = Pt(size); r.font.color.rgb = RGBColor(0x6B, 0x74, 0x88); r.font.name = 'Calibri'
    return tb


def move(sh, x=None, y=None, w=None, h=None):
    if x is not None: sh.left = Inches(x)
    if y is not None: sh.top = Inches(y)
    if w is not None: sh.width = Inches(w)
    if h is not None: sh.height = Inches(h)


FONTE = 'Fontes: SP156/SMIT, Prefeitura de São Paulo (abr a set/2026); IBGE, Censo 2022; análise própria em Python (Parte 3).'

# ---------- Slide 2: identificação ----------
s = S(2)
fill(shp(s, 'Text 3'), ['URBANIQ'])
fill(shp(s, 'Text 4'), ['**Turma 1TSCOB · Projeto UrbanIQ · Equipe DataGuy**',
                        'Uma CitizenTech de zeladoria urbana: recebe o problema pelo canal que o cidadão já usa (WhatsApp, telefone ou app), prioriza com equidade e mostra o andamento para todos.'], size=11.5)
fill(shp(s, 'Text 5'), ['TURMA 1TSCOB: INTEGRANTE'])
fill(shp(s, 'Text 7'), ['**Thiago Fiel de Oliveira**', 'RM 570088 · responsável'])
move(shp(s, 'Text 7'), x=0.1, w=2.0)
delete(s, 'Shape 8', 'Image 4', 'Text 9', 'Shape 10', 'Image 5', 'Text 11', 'Shape 12', 'Image 6', 'Text 13', 'Shape 14', 'Image 7', 'Text 15',
       'Image 2', 'Text 2')
picture_in(s, 'img/logo.png', 6.9, 1.05, 2.5, 2.0)

# ---------- Slide 3: problema ----------
s = S(3)
fill(shp(s, 'Text 2'), ['Zeladoria em São Paulo: quem chega até a Prefeitura?'])
fill(shp(s, 'Text 3'), [
    '**Território:** município de São Paulo, 32 subprefeituras e 11,45 milhões de habitantes.',
    '**Tamanho:** 245 mil pedidos de zeladoria em 6 meses, cerca de 1.340 por dia (buraco, entulho, árvore, drenagem).',
    '**Hipóteses testadas com dados reais:** H1 "a periferia espera mais": não se confirmou (mediana de 2 dias em todos os anéis). H2 "a periferia pede menos": confirmada (18,6 contra 23,9 pedidos por mil hab.; correlação de Spearman −0,61). H3 "a periferia usa mais o telefone": confirmada (28% contra 24%).',
    '**Recorte:** a desigualdade está na porta de entrada, não no atendimento. Cidade Tiradentes registra 12,6 pedidos por mil hab.; Jabaquara, 29,5.',
    '**Ainda a validar:** a causa (acesso digital, confiança ou falta de tempo), com entrevistas em associações de bairro.'], size=10)
fill(shp(s, 'Text 5'), ['Na periferia, o problema existe, mas não vira chamado.'], size=14.5)
fill(shp(s, 'Text 7'), ['**Persona: Dona Cida, 64 anos,** Cidade Tiradentes. Celular simples e pouco pacote de dados; só usa WhatsApp e áudio. Vê o entulho na esquina há semanas, não sabe onde reclamar e acha que "não adianta".',
                        'Persona ilustrativa, montada a partir dos dados.'], size=9)
move(shp(s, 'Text 3'), x=0.5, y=1.62, w=3.45, h=3.25)
for para in shp(s, 'Text 3').text_frame.paragraphs:
    for r in para.runs:
        r.font.size = Pt(8.8)
picture_in(s, 'img/mapa_slide.png', 4.0, 1.5, 2.2, 3.35)
cap = note(s, 'Onde a cidade pede menos', x=4.0, y=1.25, w=2.2, h=0.25, size=8)
cap.text_frame.paragraphs[0].runs[0].font.bold = True
cap.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1E, 0x2A, 0x4A)
cap.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
note(s, FONTE)

# ---------- Slide 4: solução ----------
s = S(4)
fill(shp(s, 'Text 2'), ['UrbanIQ: zeladoria que escuta todo território'])
fill(shp(s, 'Text 3'), [
    'Plataforma de zeladoria **omnichannel**: o cidadão relata o problema pelo canal que já usa, o sistema prioriza com um **score explicável** e todos acompanham o andamento.',
    '**1. Porta de entrada inclusiva:** WhatsApp com menu numérico e áudio, telefone 156 e agentes comunitários com registro offline.',
    '**2. Score com equidade:** risco + tempo aberto + reiterações + bônus para territórios que pedem pouco.',
    '**3. Prazo realista:** informa na abertura a chance de resolução em 7 dias para aquele serviço.',
    '**4. Transparência:** status a cada etapa e painel público só com dados agregados.'], size=10)
fill(shp(s, 'Text 7'), [
    '**O que:** plataforma web + chatbot de WhatsApp integrados ao SP156.',
    '**Como resolve:** amplia quem consegue pedir e prioriza quem mais precisa, sem piorar o prazo de ninguém.',
    '**Dados:** pedidos do SP156, Censo 2022, foto e GPS do chamado. **Entrega:** protocolo, prazo provável, status e o que foi resolvido no bairro.',
    '**Acessibilidade:** funciona por SMS e áudio, sem app e sem internet rápida; leitor de tela, alto contraste e linguagem simples.'], size=10)

# ---------- Slide 5: público e ecossistema ----------
s = S(5)
fill(shp(s, 'Text 3'), ['**Público beneficiado**',
                        '**Moradores da periferia** (idosos, PcD, pouca conexão): pedir sem app e saber o prazo.',
                        '**Cidadãos em geral:** acompanhar o pedido e ver o que foi feito no bairro.',
                        '**Gestores das subprefeituras:** fila priorizada e indicadores para decidir onde agir.',
                        '**Equipes de campo:** ordem de serviço com local e foto.'], size=9.5)
fill(shp(s, 'Text 4'), ['**Ecossistema**',
                        '**Prefeitura (SMIT e subprefeituras):** dona do SP156 e executora dos serviços.',
                        '**IBGE e portal de dados abertos:** população e histórico de chamados.',
                        '**Associações de bairro e agentes comunitários:** registram pedidos presencialmente.',
                        '**WhatsApp Business e operadoras:** canal de mensagens.',
                        '**Universidades:** validação do score e auditoria de vieses.'], size=9.5)
fill(shp(s, 'Text 7'), ['**Na prática:** Dona Cida manda um áudio pelo WhatsApp; o agente da associação confirma o local; a subprefeitura recebe o pedido já priorizado; e ela recebe um aviso a cada etapa.'], size=10)

# ---------- Slide 6: benefícios e impactos ----------
s = S(6)
fill(shp(s, 'Text 6'), [
    '**Onde:** começo pelas 11 subprefeituras do anel periférico (4,3 milhões de habitantes).',
    '**Indicadores (linha de base medida na Parte 3 → meta):**',
    '• Pedidos por mil hab. na periferia: 18,6 → 22',
    '• Diferença periferia x centro: −22% → −5%',
    '• Resolvidos em até 7 dias: 74% → manter ou subir',
    '• Reiterações do mesmo problema: 11 mil em 6 meses → reduzir',
    '**Escala:** SP156 e Censo cobrem a cidade toda; o modelo serve para qualquer município com central 156.'], size=9.5)
fill(shp(s, 'Text 10'), [
    '**Inclusão:** quem não usa portal ou app passa a ser ouvido.',
    '**Decisão baseada em dados:** o gestor vê onde o problema está escondido, não só onde há mais reclamação.',
    '**Agilidade:** fila priorizada e menos pedidos repetidos.',
    '**Confiança:** prazo e status visíveis reduzem o "não adianta reclamar".',
    '**Economia:** resolver o problema pequeno antes que vire grande (boca de lobo limpa antes da chuva).'], size=10)

# ---------- Slide 7: ODS ----------
s = S(7)
fill(shp(s, 'Text 3'), [
    '**ODS 11 (metas 11.3 e 11.6):** gestão urbana participativa e manutenção do espaço público. Indicador: % resolvido em 7 dias.',
    '**ODS 10 (meta 10.2):** inclusão de quem tem menos acesso digital. Indicador: diferença de pedidos por mil hab. entre periferia e centro.',
    '**ODS 16 (metas 16.6 e 16.7):** instituições transparentes e decisão com participação. Indicador: % de chamados com status público e avaliação.'], size=10)
fill(shp(s, 'Text 5'), ['Destaquei os ODS 10, 11 e 16, ligados diretamente ao problema.'])
escolhidos = {'10', '11', '16'}
for sh in list(s.shapes):
    if sh.name.startswith('Text ') and sh.has_text_frame and sh.text_frame.paragraphs[0].text.strip() in [str(i) for i in range(1, 18)]:
        num = sh.text_frame.paragraphs[0].text.strip()
        idx = int(sh.name.split()[1]) - 1
        bg = shp(s, f'Shape {idx}')
        if num not in escolhidos:
            bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(0xD9, 0xE1, 0xEC)
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    r.font.color.rgb = RGBColor(0x9A, 0xA3, 0xB5)
        else:
            bg.line.color.rgb = RGBColor(0xED, 0x18, 0x5C); bg.line.width = Pt(3)

# ---------- Slide 8: tecnologia ----------
s = S(8)
fill(shp(s, 'Text 3'), [
    'Escolhi tecnologias que já uso no curso e que conversam entre si, do pedido até o painel.',
    '**Coleta:** WhatsApp Business API, app, portal web e telefone 156.',
    '**Armazenamento:** Oracle para dados pessoais (isolado, LGPD) e Delta Lake no Databricks para o histórico.',
    '**Tratamento e análise:** Python (Pandas, NumPy, SciPy) e Spark, os mesmos da análise da Parte 3.',
    '**Visualização:** Power BI para o gestor e portal web para o cidadão.'], size=10)
delete(s, 'Image 1')
picture_in(s, 'img/tecnologias.png', 5.05, 1.59, 4.45, 2.61)

# ---------- Slide 9: arquitetura ----------
s = S(9)
delete(s, 'Image 1')
move(shp(s, 'Shape 2'), x=0.4, y=1.3, w=5.0, h=2.85)
picture_in(s, 'img/arquitetura.png', 0.45, 1.35, 4.9, 2.75)
move(shp(s, 'Text 3'), x=5.6, w=3.9)
move(shp(s, 'Text 4'), x=5.6, w=3.9)
fill(shp(s, 'Text 4'), [
    '**1. Fontes:** canais do cidadão (WhatsApp, 156, app, agente) e bases públicas (SP156 e Censo).',
    '**2. Ingestão:** API em tempo real para chamados novos, carga em lote para dados abertos e fila offline.',
    '**3. Armazenamento:** medalhão no Databricks (bronze, prata, ouro); dados pessoais isolados no Oracle.',
    '**4. Modelo analítico:** score com equidade territorial, previsão de prazo e alerta de subnotificação.',
    '**5. Entrega:** WhatsApp/SMS e portal para o cidadão, Power BI para o gestor, app para a equipe.'], size=9.5)

# ---------- Slide 10: protótipo ----------
s = S(10)
fill(shp(s, 'Text 2'), ['Protótipo de baixa fidelidade (3 telas)'])
fill(shp(s, 'Text 3'), [
    '**① WhatsApp:** o cidadão escolhe o problema por número ou áudio, envia foto e local e recebe protocolo com prazo provável (vem da análise de probabilidade).',
    '**② Portal do cidadão:** linha do tempo do chamado, prazo previsto, avaliação e o que foi resolvido no bairro.',
    '**③ Painel do gestor:** fila ordenada pelo score, com cada parcela explicada, inclusive o bônus de equidade.',
    'Dados das telas são ilustrativos e coerentes com os números reais do SP156.'], size=9)
move(shp(s, 'Text 3'), x=0.5, y=1.4, w=2.9, h=3.5)
delete(s, 'Text 4', 'Shape 5', 'Image 1', 'Shape 6', 'Shape 7', 'Image 2', 'Text 8')
picture_in(s, 'img/prototipo.png', 3.55, 1.0, 6.0, 3.95)

# ---------- Slide 11: uso responsável ----------
s = S(11)
fill(shp(s, 'Text 6'), [
    '**Dados pessoais:** nome e telefone só para avisos; ficam no Oracle, separados da base analítica.',
    '**Consentimento:** aceite claro na 1ª mensagem, com opção de pedido anônimo.',
    '**Anonimização:** a análise usa só agregados; no portal, o local aparece por quadra, nunca por casa.',
    '**Segurança:** perfis de acesso, criptografia e registro de quem consultou o quê (LGPD, arts. 6º e 46).'], size=10)
fill(shp(s, 'Text 10'), [
    '**Viés encontrado nos dados:** priorizar só pelo volume favorece quem mais reclama; a periferia pede 22% menos por habitante.',
    '**Correção:** bônus de equidade no score e canais sem internet (156, SMS, áudio, agente).',
    '**Monitoramento:** pedidos por mil hab. por subprefeitura, todo mês.',
    '**Limite:** o SP156 não traz idade, renda ou deficiência; isso será medido com pesquisa amostral consentida.'], size=10)

# ---------- Slide 12: painel ----------
s = S(12)
textos = {
    '5': '**Dados e KPIs:** SP156 (SMIT) + Censo 2022 (IBGE). Tratei datas em 2 formatos, padronizei subprefeituras e removi 11 mil duplicados. KPIs: total, por mil hab., mediana de dias, % em 7 dias, % telefone/WhatsApp.',
    '8': '**Visualizações:** linha (evolução mensal por anel), barras (ranking por mil hab.), mapa de bolhas (distribuição territorial) e barras 100% (canal por anel).',
    '11': '**Interatividade:** filtros por anel, subprefeitura, mês e serviço; mapa com zoom e dicas (população, prazo, canal); rótulos, legendas e cores seguras para daltonismo.',
    '14': '**3 insights:** (1) o prazo é igual no centro e na periferia; (2) a periferia pede 22% menos por habitante; (3) 34% da periferia usa telefone ou WhatsApp. Arquivo fonte (.pbix) no ZIP.'}
caixas = [('Shape 3', 'Text 4', 'Text 5'), ('Shape 6', 'Text 7', 'Text 8'), ('Shape 9', 'Text 10', 'Text 11'), ('Shape 12', 'Text 13', 'Text 14')]
for i, (bx, num, tx) in enumerate(caixas):
    y = 1.45 + i * 0.9
    move(shp(s, bx), x=0.5, y=y, w=4.15, h=0.82)
    move(shp(s, num), x=0.58, y=y + 0.12, w=0.5, h=0.5)
    move(shp(s, tx), x=1.12, y=y + 0.04, w=3.45, h=0.76)
    fill(shp(s, tx), [textos[tx.split()[1]]], size=8)
if PAINEL:
    picture_in(s, PAINEL, 4.8, 1.45, 4.75, 3.52)
else:
    ph = s.shapes.add_textbox(Inches(4.8), Inches(1.45), Inches(4.75), Inches(3.52))
    ph.text_frame.text = '[print do painel Power BI]'
note(s, 'Fontes: SP156/SMIT (abr a set/2026) e IBGE, Censo 2022.', y=5.0)

# ---------- Slide 13: link ----------
s = S(13)
fill(shp(s, 'Text 3'), [LINK])
for para in shp(s, 'Text 3').text_frame.paragraphs:
    for r in para.runs:
        r.hyperlink.address = LINK

# ---------- remover slides de exemplo (14 a 20) ----------
ids = p.slides._sldIdLst
for sld in list(ids)[13:]:
    p.part.drop_rel(sld.rId)
    ids.remove(sld)

p.save('GS_1TSCOB_Pitch_UrbanIQ_DataGuy.pptx')
print('salvo')
