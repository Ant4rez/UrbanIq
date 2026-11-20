# Roteiro do vídeo pitch · UrbanIQ (GS 2026.2)

**Duração alvo: 4min30** (limite 5min) · cerca de 600 palavras · fale em ritmo de conversa.
**Formato sugerido:** gravação de tela com o PDF do pitch em tela cheia + sua webcam no canto (OBS, Teams ou o próprio PowerPoint em "Gravar"). Avance o slide quando o roteiro indicar **[slide X]**.

---

### 0:00 a 0:25 · Abertura **[slide 2]**
> Olá, eu sou o Thiago Fiel de Oliveira, da turma 1TSCOB, equipe DataGuy. Este é o **UrbanIQ**, uma CitizenTech de zeladoria urbana. A ideia é simples: o problema da rua precisa chegar até a Prefeitura, venha de onde vier.

### 0:25 a 1:20 · O problema e a virada dos dados **[slide 3]**
> Eu comecei com uma hipótese: "na periferia de São Paulo, a Prefeitura demora mais para resolver buraco, entulho ou árvore caída". Para testar, analisei em Python **245 mil pedidos reais do SP156**, de abril a setembro de 2026, cruzados com o **Censo 2022**.
>
> E os dados me surpreenderam. O tempo de atendimento é **igual**: mediana de 2 dias no centro e na periferia. O problema está em outro lugar. A periferia registra **22% menos pedidos por habitante**. Cidade Tiradentes faz menos da metade dos pedidos do Jabaquara. Não é que lá tenha menos buraco: **o problema existe, mas não vira chamado.**
>
> É o caso da Dona Cida, 64 anos, que só usa WhatsApp e áudio, vê o entulho na esquina há semanas e acha que não adianta reclamar.

### 1:20 a 2:10 · A solução **[slide 4]** e **[slide 5]**
> Por isso o UrbanIQ ataca a **porta de entrada**. Ele é omnichannel: o cidadão abre o pedido por WhatsApp com menu numérico ou áudio, pelo telefone 156, pelo app, ou com um agente comunitário que registra até sem internet.
>
> Depois, cada pedido recebe um **score de prioridade explicável**: risco, tempo em aberto, reiterações e um **bônus de equidade** para os territórios que pedem pouco, porque ali cada pedido provavelmente representa vários problemas que ninguém relatou.
>
> E o cidadão recebe um **prazo realista** já na abertura, calculado com a probabilidade de resolução em 7 dias para aquele tipo de serviço.
>
> Quem ganha: moradores da periferia, gestores das subprefeituras e equipes de campo. Quem faz funcionar: Prefeitura, IBGE, associações de bairro e o canal WhatsApp.

### 2:10 a 2:50 · Protótipo **[slide 10]**
> Aqui estão as três telas. No WhatsApp, a Dona Cida manda foto e local e recebe protocolo com prazo. No portal, ela acompanha cada etapa e avalia o serviço. E o gestor vê a fila ordenada pelo score, com cada parcela explicada, inclusive o bônus de equidade.

### 2:50 a 3:30 · Painel e evidências **[slide 12]**
> No painel do Power BI, com filtros por território, mês e serviço, ficam claros os três insights: o prazo é igual em toda a cidade, a periferia pede 22% menos por habitante, e um terço dos pedidos da periferia chega por telefone ou WhatsApp. Ou seja, uma solução só digital deixaria de fora justamente quem já pede menos.

### 3:30 a 4:05 · Arquitetura e uso responsável **[slide 9]** e **[slide 11]**
> A arquitetura usa o que eu já trabalhei no curso: os canais e as bases públicas entram por API e por carga em lote, passam pelo medalhão no Databricks, e os dados pessoais ficam isolados no Oracle, seguindo a LGPD. A análise usa só dados agregados, e o próprio score corrige o viés de priorizar quem mais reclama.

### 4:05 a 4:30 · Impacto e fechamento **[slide 6]** e **[slide 7]**
> A meta é subir os pedidos por habitante na periferia de 18,6 para 22 por mil, sem piorar os 74% resolvidos em até uma semana. Isso conecta o UrbanIQ aos ODS 10, 11 e 16.
>
> O UrbanIQ não conserta a rua, mas garante que **toda rua seja ouvida**. Obrigado!

---

## Checklist antes de publicar
- [ ] Duração final **abaixo de 5:00**
- [ ] YouTube: visibilidade **Pública** (não "não listado", não "privado")
- [ ] Título sugerido: `GS 2026.2 | UrbanIQ | 1TSCOB | DataGuy`
- [ ] Abrir o link em **aba anônima** e confirmar que toca sem pedir login
- [ ] Me mandar o link: eu coloco no último slide do PDF e gero o `linkvideo.txt`
