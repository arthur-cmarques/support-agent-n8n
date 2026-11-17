# Agente de Triagem e Resposta de Suporte (n8n + LLM + RAG)

Agente de suporte para um marketplace de delivery **fictício**, construído em n8n. Recebe um ticket em texto livre, classifica, consulta uma base de políticas via RAG, responde com citação da fonte e **escala para um humano quando não deve decidir sozinho**.

> Projeto de portfólio. Toda a base de conhecimento, os pedidos e os tickets são **sintéticos e inventados**. Nenhum sistema interno ou política real de empresa foi usado ou copiado.

## Problema
Times de suporte de marketplaces recebem muitos tickets repetitivos (atraso, reembolso, cupom, cadastro de restaurante). Automatizar tudo é arriscado; o valor está em resolver o que é seguro e encaminhar o resto com contexto.

## Arquitetura

```
Webhook (ticket)
  → Normalizar
  → Classificar (LLM + saída estruturada: categoria, confiança, urgência, injection, gatilho)
  → Consultar pedido (mock) e decidir rota
  → Escalar antes do RAG?  ── sim → Escalonamento (resumo para humano) ─┐
        │ não                                                           │
        → Recuperar políticas (vector store, top-4)                     │
        → Gerar resposta (LLM + saída estruturada, com citação KB-xx)   │
        → Guardrail final (citação válida? limite de reembolso? resolvido?)
        → Responder ◄───────────────────────────────────────────────────┘
```

Decisões de projeto:
- **Escalar cedo economiza custo:** gatilhos de risco (jurídico, saúde, fraude, conduta, prompt injection), categoria "outro", confiança baixa ou pedido não identificado nem passam pelo RAG.
- **Guardrail pós-geração:** sem citação válida de documento recuperado, ou reembolso elegível acima de R$ 60 (limite automático da KB-04), o ticket é escalado.
- **Entrada do cliente tratada como dado**, nunca como instrução (delimitadores + regras no prompt + classificação de injection).
- **Tools mock:** a consulta de pedido é um Code node sobre `data/pedidos_mock.csv` (embutido no workflow), simulando uma API interna sem fingir conhecer sistemas reais.

## Estrutura
```
workflows/1-ingestao-kb.json          indexa kb/*.md no vector store em memória
workflows/2-triagem-e-resposta.json   agente principal (webhook)
kb/                                   17 documentos de política FICTÍCIOS (KB-01..KB-17)
data/pedidos_mock.csv                 12 pedidos sintéticos
data/tickets_teste.csv                44 tickets sintéticos + gabarito (categoria, deve_escalar, doc_correto, tipo)
eval/rodar_avaliacao.py               envia os tickets ao webhook e salva results/resultados.csv
eval/calcular_metricas.py             calcula as métricas e a matriz de confusão
docker-compose.yml                    n8n local com a pasta kb montada
```

## Como rodar
1. `docker compose up -d` e abra http://localhost:5678.
2. Importe os dois workflows (*Import from File*). Crie a credencial **OpenAI** e selecione-a nos nós de modelo e de embeddings (o JSON traz um placeholder).
3. Execute o workflow **1 Ingestao KB** manualmente (indexa os 17 documentos). O vector store é *em memória*: se o n8n reiniciar, rode a ingestão de novo.
4. Ative o workflow **2 Triagem e Resposta** e teste:
   ```bash
   curl -X POST http://localhost:5678/webhook/ticket -H "Content-Type: application/json" \
     -d '{"ticket_id":"demo1","mensagem":"Meu PED-1001 chegou 35 min atrasado, tenho direito a algo?","pedido_id":"PED-1001"}'
   ```
5. Avaliação: `python eval/rodar_avaliacao.py --url http://localhost:5678/webhook/ticket` e depois `python eval/calcular_metricas.py`.

## Dataset de teste
44 tickets escritos e rotulados à mão: 24 claros (inclui 1 que deve escalar por limite de valor), 8 ambíguos, 5 fora de escopo, 4 com cliente furioso/gatilho de risco e 3 tentativas de prompt injection. Os casos difíceis existem de propósito: um dataset só com casos fáceis não mede nada.

## Métricas
| Métrica | O que mede |
|---|---|
| Acerto de classificação | categoria prevista vs. `categoria_real`, com matriz de confusão |
| **Auto-resolvido errado** | casos que deveriam escalar e foram respondidos sozinhos (a mais importante) |
| Recall de escalonamento | casos que deveriam escalar e escalaram |
| Escalonamento desnecessário | casos resolvíveis que foram escalados |
| % resolvido sem humano | só faz sentido lido junto com "auto-resolvido errado" |
| Retrieval hit@4 | o documento correto estava entre os 4 recuperados |
| Citação correta | o auto-resolvido citou o documento esperado |
| Custo e latência | custo **estimado** (caracteres/4) e latência medida pelo cliente |

## Resultados
**Ainda não medidos.** Rode a avaliação e cole aqui o conteúdo de `results/metricas.md`, com data, modelo e temperatura usados. Rode ao menos 2 vezes e registre a variação.

Conferência manual recomendada: leia as respostas dos tickets auto-resolvidos (≈24) e marque fiel à política / cita fonte / tom adequado. Se usar um LLM como juiz, valide uma amostra de 10 à mão e diga isso aqui.

## Limitações (leia antes de generalizar)
- Dados 100% sintéticos, escritos pelo próprio autor: o resultado mostra que o fluxo funciona, não que resolveria X% de tickets reais.
- n = 44; uma diferença de 1 ticket muda ~2 p.p.
- Tokens e custo são estimativas, não o consumo faturado.
- Vector store em memória (sem persistência); sem autenticação no webhook; sem fila humana real (o escalonamento devolve um resumo na resposta).
- Gabarito e KB têm o mesmo autor, o que favorece o acerto de retrieval.

## Próximos passos
Nó *Send and Wait for Response* para aprovação humana de reembolsos; envio do resumo ao atendente via Telegram/e-mail; vector store persistente (Qdrant/pgvector); avaliação com LLM-as-judge validada.
