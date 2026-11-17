"""Envia cada ticket de data/tickets_teste.csv ao webhook do n8n e salva results/resultados.csv.

Uso:
    python eval/rodar_avaliacao.py --url http://localhost:5678/webhook/ticket
(para testes use a Production URL do webhook, com o workflow ATIVADO)
"""
import argparse, csv, json, os, time, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True)
ap.add_argument("--tickets", default="data/tickets_teste.csv")
ap.add_argument("--out", default="results/resultados.csv")
a = ap.parse_args()

os.makedirs(os.path.dirname(a.out), exist_ok=True)
CAMPOS = ["ticket_id", "decisao", "categoria_prevista", "confianca", "motivo_escalonamento",
          "docs_recuperados", "docs_citados", "tokens_estimados", "custo_estimado_usd",
          "latencia_s", "resposta_ao_cliente", "erro"]

with open(a.tickets, encoding="utf-8") as f, open(a.out, "w", newline="", encoding="utf-8") as g:
    w = csv.DictWriter(g, fieldnames=CAMPOS)
    w.writeheader()
    for t in csv.DictReader(f):
        body = json.dumps({"ticket_id": t["ticket_id"], "mensagem": t["mensagem"], "pedido_id": t["pedido_id"]}).encode()
        req = urllib.request.Request(a.url, data=body, headers={"Content-Type": "application/json"})
        row = {"ticket_id": t["ticket_id"]}
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
            if isinstance(d, list): d = d[0]
            for k in CAMPOS:
                if k in d:
                    row[k] = "|".join(d[k]) if isinstance(d[k], list) else d[k]
        except Exception as e:
            row["erro"] = str(e)[:200]
        row["latencia_s"] = round(time.time() - t0, 2)
        w.writerow(row)
        print(t["ticket_id"], row.get("decisao", "ERRO"), row["latencia_s"], "s")
print("salvo em", a.out)
