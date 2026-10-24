"""Aggregate the songs-LDA outputs behind the JNE 2026 slides into data.js.

Usage: python -I build_data.py <songs-LDA root>
"""
import csv, json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
rd = lambda p: list(csv.DictReader(open(root / p, encoding="utf-8-sig", newline="")))
r4 = lambda x: round(float(x), 4)

prev = rd("data/stm_prevalence_by_year.csv")
years = [int(r["year"]) for r in prev]
out = {
    "years": years,
    "nSongs": [int(r["n_songs"]) for r in prev],
    "prevalence": {k: [r4(r[f"Topic{k}"]) for r in prev] for k in range(1, 9)},
}

# spline curves, thinned to every 4th point (+ last)
curves = {}
for r in rd("data/stm_year_effect_curves.csv"):
    curves.setdefault(int(r["topic_num"]), []).append([float(r["year"]), r4(r["expected"]), r4(r["ci_lo"]), r4(r["ci_hi"])])
out["curves"] = {k: [p for i, p in enumerate(v) if i % 4 == 0 or i == len(v) - 1] for k, v in curves.items()}
for v in out["curves"].values():
    for p in v: p[0] = round(p[0], 2)

words = {}
for r in rd("data/stm_results/topic_word_probs.csv"):
    if int(r["rank"]) <= 25:
        words.setdefault(int(r["topic"]), []).append([r["word"], r4(r["prob"])])
out["words"] = words

out["corr"] = [[int(r["topic_i"]), int(r["topic_j"]), r4(r["cor"])]
               for r in rd("data/stm_results/topic_correlations.csv") if float(r["posadj"]) > 0]
out["frontierTopics"] = [[int(r["K"]), int(r["topic"]), r4(r["semcoh"]), r4(r["exclus"])] for r in rd("data/stm_results/frontier_topics.csv")]
out["frontierMeans"] = [[int(r["K"]), r4(r["semcoh"]), r4(r["exclus"])] for r in rd("data/stm_results/frontier_means.csv")]
out["searchK"] = [{k: r4(r[k]) for k in ("K", "heldout", "residual", "semcoh", "lbound")} for r in rd("data/stm_results/searchk_diagnostics.csv")]

ids = {"Naturaleza y Ensueño": 1, "Gánster Lifestyle": 2, "Fiesta y Baile": 3, "Sátira y Cultura Popular": 4,
       "Perreo y Deseo": 5, "Desamor y Nostalgia": 6, "Protesta y Crítica Social": 7, "Culpa y Reflexión": 8}
forest = {}
for r in rd("presentations/JNE2026/jne2026_numbers.csv"):
    if not r["claim"].startswith("Δθ") or "bootstrap_changes" not in r["source"]:
        continue
    m = re.match(r"Δθ (.+) \[(\w+)\]", r["claim"])
    c = re.match(r"([+-]?[\d.]+)\s*\[([+-]?[\d.]+),\s*([+-]?[\d.]+)\]", r["value"])
    if m and c and m[1] in ids and m[2] in ("song_weighted", "artist_weighted", "frame_reweighted"):
        forest.setdefault(m[2], {})[ids[m[1]]] = [float(x) for x in c.groups()]
out["forest"] = forest

(Path(__file__).parent / "data.js").write_text("window.JNE = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print({k: (len(v) if hasattr(v, "__len__") else v) for k, v in out.items()}, {k: len(v) for k, v in forest.items()})
