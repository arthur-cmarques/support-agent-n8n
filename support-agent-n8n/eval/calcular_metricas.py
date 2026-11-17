"""Calcula métricas a partir de data/tickets_teste.csv (gabarito) + results/resultados.csv.

Uso: python eval/calcular_metricas.py
Gera results/metricas.md e results/matriz_confusao.csv
"""
import argparse, csv, statistics
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--tickets", default="data/tickets_teste.csv")
ap.add_argument("--resultados", default="results/resultados.csv")
ap.add_argument("--out-md", default="results/metricas.md")
ap.add_argument("--out-cm", default="results/matriz_confusao.csv")
a = ap.parse_args()

gab = {r["ticket_id"]: r for r in csv.DictReader(open(a.tickets, encoding="utf-8"))}
res = {r["ticket_id"]: r for r in csv.DictReader(open(a.resultados, encoding="utf-8"))}
ids = [i for i in gab if i in res and not res[i].get("erro") and res[i].get("decisao")]
erros = [i for i in gab if i not in ids]
n = len(ids)

def pct(x, d): return f"{100 * x / d:.1f}% ({x}/{d})" if d else "n/a"

# 1) classificação
ok_cls = sum(res[i]["categoria_prevista"] == gab[i]["categoria_real"] for i in ids)
cats = sorted({gab[i]["categoria_real"] for i in ids} | {res[i]["categoria_prevista"] for i in ids})
cm = Counter((gab[i]["categoria_real"], res[i]["categoria_prevista"]) for i in ids)
with open(a.out_cm, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["real\\previsto"] + cats)
    for r in cats: w.writerow([r] + [cm[(r, c)] for c in cats])

# 2) decisão
auto = [i for i in ids if res[i]["decisao"] == "auto_resolvido"]
esc = [i for i in ids if res[i]["decisao"] == "escalado"]
deve = [i for i in ids if gab[i]["deve_escalar"] == "sim"]
nao_deve = [i for i in ids if gab[i]["deve_escalar"] == "nao"]
auto_errado = [i for i in deve if res[i]["decisao"] == "auto_resolvido"]
esc_desnec = [i for i in nao_deve if res[i]["decisao"] == "escalado"]
rec_esc = sum(res[i]["decisao"] == "escalado" for i in deve)

# 3) retrieval (só onde o RAG rodou e há doc esperado)
rag = [i for i in ids if res[i].get("docs_recuperados") and gab[i]["doc_correto"].startswith("KB-")]
hit = sum(gab[i]["doc_correto"] in res[i]["docs_recuperados"].split("|") for i in rag)

# 4) citação correta nos auto-resolvidos
cit = [i for i in auto if gab[i]["doc_correto"].startswith("KB-")]
cit_ok = sum(gab[i]["doc_correto"] in res[i].get("docs_citados", "").split("|") for i in cit)

# 5) custo e latência
def nums(k): return [float(res[i][k]) for i in ids if res[i].get(k) not in (None, "")]
lat, custo = nums("latencia_s"), nums("custo_estimado_usd")
def p(v, q): s = sorted(v); return s[min(len(s) - 1, int(q * len(s)))] if s else float("nan")

# 6) por tipo
por_tipo = defaultdict(lambda: [0, 0, 0])  # total, decisao certa, classificação certa
for i in ids:
    t = gab[i]["tipo"]
    certa = (res[i]["decisao"] == "escalado") == (gab[i]["deve_escalar"] == "sim")
    por_tipo[t][0] += 1; por_tipo[t][1] += certa
    por_tipo[t][2] += res[i]["categoria_prevista"] == gab[i]["categoria_real"]

L = [f"# Métricas — {n} tickets SINTÉTICOS rotulados manualmente\n",
     f"Tickets sem resposta válida (erros): {len(erros)} {erros if erros else ''}\n",
     "| Métrica | Resultado |", "|---|---|",
     f"| Acerto de classificação | {pct(ok_cls, n)} |",
     f"| **Auto-resolvido errado** (deveria escalar e respondeu sozinho) | {pct(len(auto_errado), len(deve))} {auto_errado} |",
     f"| Recall de escalonamento (deveria escalar e escalou) | {pct(rec_esc, len(deve))} |",
     f"| Escalonamento desnecessário (poderia resolver e escalou) | {pct(len(esc_desnec), len(nao_deve))} {esc_desnec} |",
     f"| % resolvido sem humano (auto-resolvidos / total) | {pct(len(auto), n)} |",
     f"| Taxa de escalonamento | {pct(len(esc), n)} |",
     f"| Retrieval hit@4 (onde o RAG rodou) | {pct(hit, len(rag))} |",
     f"| Citação do doc correto nos auto-resolvidos | {pct(cit_ok, len(cit))} |",
     f"| Custo médio por ticket (ESTIMADO) | US$ {statistics.mean(custo):.5f} |" if custo else "| Custo médio | n/a |",
     f"| Latência p50 / p95 | {p(lat, .5):.1f}s / {p(lat, .95):.1f}s |" if lat else "| Latência | n/a |",
     "", "## Por tipo de ticket", "| Tipo | n | Decisão correta | Classificação correta |", "|---|---|---|---|"]
for t, (tot, d, c) in sorted(por_tipo.items()):
    L.append(f"| {t} | {tot} | {pct(d, tot)} | {pct(c, tot)} |")
L += ["", "Observações: dataset sintético e pequeno; custo e tokens são estimativas (caracteres/4);",
      "a qualidade textual das respostas auto-resolvidas deve ser conferida manualmente (ver README)."]
open(a.out_md, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
