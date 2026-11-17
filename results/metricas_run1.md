# Métricas — 44 tickets SINTÉTICOS rotulados manualmente

Tickets sem resposta válida (erros): 0 

| Métrica | Resultado |
|---|---|
| Acerto de classificação | 84.1% (37/44) |
| **Auto-resolvido errado** (deveria escalar e respondeu sozinho) | 0.0% (0/19) [] |
| Recall de escalonamento (deveria escalar e escalou) | 100.0% (19/19) |
| Escalonamento desnecessário (poderia resolver e escalou) | 56.0% (14/25) ['T01', 'T03', 'T06', 'T07', 'T09', 'T12', 'T14', 'T15', 'T17', 'T20', 'T21', 'T22', 'T24', 'T25'] |
| % resolvido sem humano (auto-resolvidos / total) | 25.0% (11/44) |
| Taxa de escalonamento | 75.0% (33/44) |
| Retrieval hit@4 (onde o RAG rodou) | 100.0% (18/18) |
| Citação do doc correto nos auto-resolvidos | 100.0% (11/11) |
| Custo médio por ticket (ESTIMADO) | US$ 0.00021 |
| Latência p50 / p95 | 2.1s / 5.2s |

## Por tipo de ticket
| Tipo | n | Decisão correta | Classificação correta |
|---|---|---|---|
| ambiguo | 8 | 87.5% (7/8) | 75.0% (6/8) |
| claro | 23 | 43.5% (10/23) | 91.3% (21/23) |
| fora_escopo | 5 | 100.0% (5/5) | 80.0% (4/5) |
| furioso | 4 | 100.0% (4/4) | 50.0% (2/4) |
| injection | 3 | 100.0% (3/3) | 100.0% (3/3) |
| limite | 1 | 100.0% (1/1) | 100.0% (1/1) |

Observações: dataset sintético e pequeno; custo e tokens são estimativas (caracteres/4);
a qualidade textual das respostas auto-resolvidas deve ser conferida manualmente (ver README).
