"""Token Clock: Stockfish analysis of LLM chess games.

For every position: engine evaluation (side to move), number of candidate moves within 40 cp of the best.
For every move played: centipawn loss (0 when the move is the engine's first choice; raw difference kept in cpl_raw), quality class, output tokens, seconds.

Usage: python analyse.py <games.json> <out.csv> [nodes] [stockfish_path]
"""
import json, csv, sys, chess, chess.engine

SRC, OUT = sys.argv[1], sys.argv[2]
NODES = int(sys.argv[3]) if len(sys.argv) > 3 else 1500000
SF = sys.argv[4] if len(sys.argv) > 4 else "stockfish"
CAP = 1000  # centipawn cap applied to mate and decisive scores

d = json.load(open(SRC))
eng = chess.engine.SimpleEngine.popen_uci(SF)
eng.configure({"Threads": 2, "Hash": 512})


def cp(score):
    v = score.relative.score(mate_score=100000)
    return max(-CAP, min(CAP, v))


def analyse(board):
    if board.is_game_over():
        return None
    info = eng.analyse(board, chess.engine.Limit(nodes=NODES), multipv=5)
    evs = [cp(e["score"]) for e in info]
    best = evs[0]
    return dict(best=best, second=evs[1] if len(evs) > 1 else "", cand=sum(1 for e in evs if best - e <= 40),
                bestmove=info[0]["pv"][0], legal=board.legal_moves.count())


rows = []
for g in d:
    G = d[g]; board = chess.Board()
    pre = analyse(board)
    for i, m in enumerate(G["moves"]):
        mv = board.parse_san(m["san"])
        npieces = len(board.piece_map())
        is_best = (mv == pre["bestmove"])
        best_san = board.san(pre["bestmove"])
        board.push(mv)
        post = analyse(board)
        played = (CAP if board.is_checkmate() else 0) if post is None else -post["best"]
        cpl_raw = max(0, pre["best"] - played)
        # The engine's own first choice cannot lose value: any difference is search noise between two evaluations.
        cpl = 0 if is_best else cpl_raw
        ply = i + 1
        phase = "opening" if ply <= 20 else ("endgame" if npieces <= 12 else "middlegame")
        cls = ("best" if cpl <= 10 else "good" if cpl <= 50 else "inaccuracy" if cpl <= 100
               else "mistake" if cpl <= 300 else "blunder")
        rows.append(dict(game=g, set=G["set"], ply=ply, player=m["player"], model=m["model"], effort=m["effort"],
                         san=m["san"], engine_best=best_san, played_engine_best=int(is_best),
                         output_tokens=m["output_tokens"],
                         reasoning_tokens="" if m.get("reasoning_tokens") is None else m["reasoning_tokens"],
                         seconds=m["seconds"], eval_before=pre["best"], eval_second=pre["second"], eval_after=played,
                         cpl=cpl, cpl_raw=cpl_raw, cls=cls, candidates_within_40cp=pre["cand"], legal_moves=pre["legal"],
                         pieces=npieces, phase=phase))
        pre = post
    print("game", g, "done", len(G["moves"]), flush=True)
eng.quit()
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("rows", len(rows))
