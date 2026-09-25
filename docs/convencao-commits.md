# Convenção de Commits — UrbanIQ

Padrão para as mensagens de commit do projeto, baseado em
[Conventional Commits](https://www.conventionalcommits.org/pt-br/) e adaptado ao português.
O objetivo é um histórico que se leia como um diário técnico do projeto: claro para o
professor, para recrutadores que visitam o portfólio e para você mesmo daqui a seis meses.

---

## Formato

```
tipo(escopo): verbo no infinitivo + o quê

Por que a mudança foi feita, em 1 a 3 linhas.
- detalhe relevante
- outro detalhe relevante
```

| Parte | Regra |
|---|---|
| **Assunto** (1ª linha) | Até ~60 caracteres (máximo 72). Sem ponto final. Letra minúscula após os dois-pontos. |
| **Verbo** | Sempre no **infinitivo**: adicionar, corrigir, atualizar, remover, reorganizar. |
| **Acentuação** | Sempre **com acento** — o Git trabalha em UTF-8 sem problema. |
| **Linha 2** | Sempre em branco (separa assunto do corpo). |
| **Corpo** | Opcional em commits pequenos, recomendado nos grandes. Explica o **porquê**. Listas com `- `, sem linha em branco entre os itens. |
| **Tom** | Técnico e factual. Descreva o que mudou, não avalie ("executivo", "realista", "completo"). |

---

## Tipos

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Entrega nova: notebook, painel, script, dashboard | `feat(fase5): adicionar painel Streamlit do 3º desafio` |
| `fix` | Correção de erro em código, dado ou cálculo | `fix(dados): corrigir CEPs sem zero à esquerda` |
| `docs` | README, PDFs de entrega, guias, textos, evidências | `docs(readme): documentar a fase 5` |
| `refactor` | Reorganizar sem mudar o resultado (pastas, nomes, limpeza de código) | `refactor: padronizar nomes de pastas por fase` |
| `data` | Novas massas de dados ou regeneração de CSVs | `data(dashboard): regenerar tb_chamado com coordenadas por bairro` |
| `chore` | Configuração: `.gitignore`, `.gitattributes`, dependências, licença | `chore: registrar dependências no requirements.txt` |

> `data` não é um tipo oficial do Conventional Commits, mas é útil num projeto de dados.
> Se preferir ficar só nos oficiais, use `feat` para dados novos e `fix` para correções.

## Escopos

Use **sempre** um escopo quando a mudança for de uma área específica:

`fase1` … `fase7` · `dashboard` · `readme` · `ddl` · `dados` · `notebook`

Mudanças que afetam o repositório todo (ex.: `.gitignore`) podem ficar sem escopo.

---

## Um assunto por commit

Se o assunto precisa de "e" para caber tudo, provavelmente são dois commits.

❌ Um commit com 180 arquivos misturando reorganização de pastas, fase 4, `.gitignore` e remoção de material:
```
refactor: reorganizar estrutura por fase e padronizar nomenclatura
```

✅ Separado:
```
refactor: reorganizar pastas por fase e padronizar nomes
feat(fase4): adicionar consulta Q2 de bairros premium
chore: bloquear arquivos .txt no .gitignore contra vazamento de credenciais
chore: remover material didático da FIAP do repositório
```

Dica: `git add <arquivo>` (em vez de `git add .`) permite montar cada commit só com os arquivos daquele assunto.

---

## Antes e depois (exemplos reais do histórico)

| Antes | Problema | Depois |
|---|---|---|
| `atualiza o README.md e o arquivo .gitattributes` | Sem tipo, vago, e alterou o `.pbix` sem mencionar | `docs(readme): atualizar seções e ajustar .gitattributes` + corpo citando o `.pbix` |
| `feat: completar notebook da fase 5 com parte 0, parte 3 e saidas de execucao` | 76 caracteres, sem acento | `feat(fase5): completar notebook com partes 0 e 3` |
| `chore: editar typo do README e remover imagem smart-city não utilizada` | Tipo errado, mistura de idiomas | `docs(readme): corrigir erro de digitação e remover imagem sem uso` |
| `docs: adiciona README, gitignore e arquitetura do projeto~` | Verbo no presente, "~" sobrando | `docs: adicionar README, .gitignore e arquitetura do projeto` |
| `chore: registrar dependencias e liberar requirements no gitignore` | Sem acento | `chore: registrar dependências e liberar requirements no .gitignore` |

## Bons exemplos do próprio histórico

```
feat: juntar parte 2 no notebook unico da fase 5

Analise estatistica dos quatro elos da cadeia de valor do COU:
teste t, ANOVA, qui-quadrado, correlacao de Pearson, Spearman e
Kendall, alem de limites, derivadas e integrais com SymPy.
```
Corpo curto que diz **o que** foi feito e **com quais ferramentas** (só faltaram os acentos).

```
chore: adicionar LICENSE MIT e .gitattributes

- LICENSE MIT permite reuso do código com atribuição
- .gitattributes normaliza line endings e classifica binários
```
Cada item explica o **porquê** da mudança.

---

## Usando o modelo `.gitmessage`

A raiz do repositório tem um arquivo `.gitmessage` com um lembrete desta convenção.
Para o Git abrir esse modelo sempre que você rodar `git commit` (sem `-m`), rode **uma vez**:

```bash
git config commit.template .gitmessage
```

A partir daí, `git commit` abre o editor já com o modelo. As linhas que começam com `#`
são só instruções e são descartadas automaticamente. Se você usar `git commit -m "..."`,
o modelo não aparece, mas as regras continuam valendo.

## Checklist rápido

- [ ] Tipo e escopo corretos?
- [ ] Verbo no infinitivo, com acento?
- [ ] Assunto com até ~60 caracteres, sem ponto final?
- [ ] Um assunto só por commit?
- [ ] Arquivos binários alterados (`.pbix`, `.pdf`, `.xlsx`) citados no corpo?
- [ ] Texto factual, sem adjetivos de propaganda?
