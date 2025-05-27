import hashlib
import os
import time
from multiprocessing import Process, Queue, cpu_count

# ─── 設定 ────────────────────────────────────────────
MESSAGE           = "Hello, blockchain!"   # 任意メッセージ
DIFFICULTY        = 8                      # 先頭に '0' が DIFFICULTY 個
USE_MULTIPROCESS  = False                   # ← ここを False にすれば単一プロセスモード
PREFIX            = "0" * DIFFICULTY
MAX_CORES         = cpu_count()
N_WORKERS         = max(2, MAX_CORES - 4) if USE_MULTIPROCESS else 1

# ─── 共通の計算ロジック ─────────────────────────────
def find_nonce(start_nonce: int, step: int, stop_check, result_callback):
    nonce = start_nonce
    tried = 0
    while True:
        if stop_check():
            return
        h = hashlib.sha256(f"{MESSAGE}{nonce}".encode()).hexdigest()
        if h.startswith(PREFIX):
            result_callback(nonce, tried + 1, h)
            return
        nonce += step
        tried += 1

# ─── マルチプロセス用ワーカープロセス ───────────────
def worker(start_nonce: int, step: int, out_q: Queue) -> None:
    def stop_check():
        return not out_q.empty()

    def result_callback(nonce, tried, h):
        out_q.put((nonce, tried, h))

    find_nonce(start_nonce, step, stop_check, result_callback)

# ─── メイン処理 ────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Mode: {'Multi-process' if USE_MULTIPROCESS else 'Single process'}")
    print(f"⏩ 使用コア数: {N_WORKERS} / 最大: {MAX_CORES}")
    print(f"🎯 難易度: {DIFFICULTY} → prefix = '{PREFIX}'")

    start = time.time()

    if USE_MULTIPROCESS:
        result_q: Queue = Queue()

        # ワーカープロセスを起動
        procs = [
            Process(target=worker, args=(i, N_WORKERS, result_q), daemon=True)
            for i in range(N_WORKERS)
        ]
        for p in procs:
            p.start()

        nonce, tried, h = result_q.get()
        elapsed = time.time() - start

        for p in procs:
            p.terminate()
            p.join()

        total_tried = tried * N_WORKERS

    else:
        # 単一プロセスで探索
        result_holder = {}

        def stop_check():
            return bool(result_holder)

        def result_callback(nonce, tried, h):
            result_holder['nonce'] = nonce
            result_holder['tried'] = tried
            result_holder['hash'] = h

        find_nonce(0, 1, stop_check, result_callback)
        elapsed = time.time() - start

        nonce = result_holder['nonce']
        tried = result_holder['tried']
        h = result_holder['hash']
        total_tried = tried

    # 結果表示
    print("\n✅  FOUND!")
    print(f"🔢 nonce        = {nonce}")
    print(f"🔑 hash         = {h}")
    print(f"🧮 total trials = {total_tried:,}")
    print(f"⏱️ elapsed      = {elapsed:.2f} s")
