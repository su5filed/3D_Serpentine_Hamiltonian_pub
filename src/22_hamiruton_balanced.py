import math
import os
from itertools import product
from random import Random

import matplotlib.pyplot as plt


# ============================================================
# 1. 素数判定
# ============================================================
def sieve_primes(n):
    """
    1..n の素数判定表を返す。
    is_prime[k] = True なら k は素数。
    """
    if n < 2:
        return [False] * (n + 1)

    is_prime = [True] * (n + 1)
    is_prime[0] = False
    is_prime[1] = False

    limit = int(math.isqrt(n))
    for p in range(2, limit + 1):
        if is_prime[p]:
            for x in range(p * p, n + 1, p):
                is_prime[x] = False

    return is_prime


# ============================================================
# 2. 近傍
# ============================================================
def neighbors_3d(p, L):
    """
    3D格子上の隣接点を返す。
    戻り値: (next_point, direction)
      direction は "x", "y", "z"
    """
    x, y, z = p

    dirs = [
        (1, 0, 0, "x"),
        (-1, 0, 0, "x"),
        (0, 1, 0, "y"),
        (0, -1, 0, "y"),
        (0, 0, 1, "z"),
        (0, 0, -1, "z"),
    ]

    for dx, dy, dz, d in dirs:
        q = (x + dx, y + dy, z + dz)
        if 0 <= q[0] < L and 0 <= q[1] < L and 0 <= q[2] < L:
            yield q, d


# ============================================================
# 3. 方向均衡寄りハミルトン路生成
# ============================================================
def hamiltonian_balanced_greedy_3d(
    L,
    seed=42,
    max_restarts=300,
    start=(0, 0, 0),
):
    """
    方向均衡寄りの 3D ハミルトン路を探索的に作る。

    方針:
      - Warnsdorff風に「次の候補の先の自由度」が少ない点を優先
      - ただし x, y, z の移動回数がなるべく均等になるようにする
      - 失敗したら乱数を変えて再試行

    注意:
      これは証明付き構成ではなく、探索型生成器。
      生成後に verify_hamiltonian_path() で必ず検証する。
    """
    N = L ** 3
    all_points = {(x, y, z) for x in range(L) for y in range(L) for z in range(L)}

    if start not in all_points:
        raise ValueError(f"start が範囲外です: {start}")

    for restart in range(max_restarts):
        rng = Random(seed + restart * 1000003)

        current = start
        unvisited = set(all_points)
        unvisited.remove(current)

        path = [current]
        move_counts = {"x": 0, "y": 0, "z": 0}

        failed = False

        for step in range(N - 1):
            candidates = []

            for q, d in neighbors_3d(current, L):
                if q not in unvisited:
                    continue

                # q に進んだ後、さらに進める未訪問近傍の数
                onward = 0
                for qq, _ in neighbors_3d(q, L):
                    if qq in unvisited and qq != current:
                        onward += 1

                # この一手を採用した場合の方向カウント
                tmp_counts = dict(move_counts)
                tmp_counts[d] += 1

                imbalance = max(tmp_counts.values()) - min(tmp_counts.values())
                used_this_dir = move_counts[d]

                # スコア:
                # 1. onward が少ない候補を優先
                # 2. 方向カウントの偏りが小さい候補を優先
                # 3. まだ少ない方向を優先
                # 4. 最後に乱数でタイブレーク
                score = (
                    onward,
                    imbalance,
                    used_this_dir,
                    rng.random(),
                )

                candidates.append((score, q, d))

            if not candidates:
                failed = True
                break

            candidates.sort(key=lambda x: x[0])
            _, next_point, direction = candidates[0]

            current = next_point
            unvisited.remove(current)
            path.append(current)
            move_counts[direction] += 1

        if not failed and len(path) == N:
            return path, move_counts, restart

    raise RuntimeError(
        f"方向均衡ハミルトン路の生成に失敗しました。L={L}, max_restarts={max_restarts}"
    )


# ============================================================
# 4. ハミルトン路チェック
# ============================================================
def verify_hamiltonian_path(path, L):
    n = L ** 3

    if len(path) != n:
        return False, f"頂点数不一致: {len(path)} != {n}"

    if len(set(path)) != n:
        return False, "同じ格子点を2回以上通っています"

    for i in range(len(path) - 1):
        a = path[i]
        b = path[i + 1]
        manhattan = abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        if manhattan != 1:
            return False, f"{i}->{i+1} が隣接していません: {a} -> {b}"

    return True, "OK"


def count_move_directions(path):
    counts = {"x": 0, "y": 0, "z": 0}

    for a, b in zip(path[:-1], path[1:]):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        dz = abs(a[2] - b[2])

        if dx == 1:
            counts["x"] += 1
        elif dy == 1:
            counts["y"] += 1
        elif dz == 1:
            counts["z"] += 1

    return counts


# ============================================================
# 5. 数字配置・素数点抽出
# ============================================================
def assign_numbers_to_path(path):
    number_to_coord = {}
    coord_to_number = {}

    for i, coord in enumerate(path, start=1):
        number_to_coord[i] = coord
        coord_to_number[coord] = i

    return number_to_coord, coord_to_number


def collect_prime_points(L, path):
    N = L ** 3
    is_prime = sieve_primes(N)
    number_to_coord, coord_to_number = assign_numbers_to_path(path)

    prime_points = []
    prime_numbers = []

    for n in range(1, N + 1):
        if is_prime[n]:
            coord = number_to_coord[n]
            prime_points.append(coord)
            prime_numbers.append(n)

    return prime_points, prime_numbers, number_to_coord, coord_to_number


# ============================================================
# 6. 3D可視化
# ============================================================
def plot_prime_3d_balanced(
    L,
    path,
    prime_points,
    save_path=None,
    show_path=True,
):
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection="3d")

    all_points = list(product(range(L), range(L), range(L)))

    ax.scatter(
        [p[0] for p in all_points],
        [p[1] for p in all_points],
        [p[2] for p in all_points],
        s=10,
        alpha=0.10,
        label="all lattice points",
    )

    if show_path:
        ax.plot(
            [p[0] for p in path],
            [p[1] for p in path],
            [p[2] for p in path],
            linewidth=0.8,
            alpha=0.25,
            label="balanced Hamiltonian path",
        )

    ax.scatter(
        [p[0] for p in prime_points],
        [p[1] for p in prime_points],
        [p[2] for p in prime_points],
        s=38,
        alpha=0.95,
        marker="o",
        label="primes",
    )

    ax.set_title(f"3D Prime Pattern on Balanced Hamiltonian Lattice L={L}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_xlim(0, L - 1)
    ax.set_ylim(0, L - 1)
    ax.set_zlim(0, L - 1)
    ax.set_box_aspect((L, L, L))
    ax.legend()

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=220, bbox_inches="tight")
        print(f"保存しました: {save_path}")

    plt.close(fig)


# ============================================================
# 7. x+y+z 平面ごとの素数密度
# ============================================================
def analyze_diagonal_planes(L, coord_to_number):
    N = L ** 3
    is_prime = sieve_primes(N)

    plane_total = {}
    plane_prime = {}

    for x in range(L):
        for y in range(L):
            for z in range(L):
                s = x + y + z
                n = coord_to_number[(x, y, z)]

                plane_total[s] = plane_total.get(s, 0) + 1
                if is_prime[n]:
                    plane_prime[s] = plane_prime.get(s, 0) + 1

    print("=" * 80)
    print("x+y+z 斜め平面ごとの素数密度")
    print("s | total | prime | density | parity")
    print("-" * 60)

    for s in sorted(plane_total.keys()):
        total = plane_total[s]
        prime = plane_prime.get(s, 0)
        density = prime / total if total > 0 else 0.0
        parity = "even" if s % 2 == 0 else "odd"

        print(f"{s:2d} | {total:5d} | {prime:5d} | {density:7.3f} | {parity}")


# ============================================================
# 8. mod 剰余ピーク解析
# ============================================================
def analyze_mod_residue_peaks_by_plane(L, coord_to_number, mod_value=7):
    """
    各偶数 s=x+y+z 平面について、
    3以上の奇数 n の mod 分布ピークを調べる。
    """
    print("=" * 80)
    print(f"mod {mod_value} 剰余ピーク解析")
    print(f"L = {L}")
    print()
    print("s | cand | peak_r | peak_count | peak_rate | r0_count | r0_rate | expected_peak")
    print("-" * 100)

    for s in range(0, 3 * (L - 1) + 1):
        if s % 2 != 0:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        counts = [0] * mod_value
        for n in nums:
            counts[n % mod_value] += 1

        cand = len(nums)
        peak_count = max(counts)
        peak_r = counts.index(peak_count)
        peak_rate = peak_count / cand

        r0_count = counts[0]
        r0_rate = r0_count / cand

        expected_peak = (s + 1) % mod_value
        mark = "OK" if peak_r == expected_peak else "--"

        print(
            f"{s:2d} | "
            f"{cand:4d} | "
            f"{peak_r:6d} | "
            f"{peak_count:10d} | "
            f"{peak_rate:9.3f} | "
            f"{r0_count:8d} | "
            f"{r0_rate:7.3f} | "
            f"{expected_peak:13d} {mark}"
        )


def summarize_peak_match_rate(L, coord_to_number, mod_value=7, min_candidates=10):
    """
    peak_r == (s+1) % mod_value
    がどれくらい成立するかを集計する。
    """
    total = 0
    match = 0

    for s in range(0, 3 * (L - 1) + 1):
        if s % 2 != 0:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if len(nums) < min_candidates:
            continue

        counts = [0] * mod_value
        for n in nums:
            counts[n % mod_value] += 1

        peak_count = max(counts)
        peak_r = counts.index(peak_count)
        expected = (s + 1) % mod_value

        total += 1
        if peak_r == expected:
            match += 1

    rate = match / total if total > 0 else 0.0

    return match, total, rate


# ============================================================
# 9. 方向均衡型の実験
# ============================================================
def run_balanced_experiment(
    L=8,
    mod_values=(3, 5, 7, 11),
    seed=42,
    max_restarts=300,
):
    print("\n" + "=" * 100)
    print(f"Balanced Hamiltonian experiment: L={L}")
    print("=" * 100)

    path, move_counts, restart_used = hamiltonian_balanced_greedy_3d(
        L=L,
        seed=seed,
        max_restarts=max_restarts,
        start=(0, 0, 0),
    )

    ok, msg = verify_hamiltonian_path(path, L)
    print("ハミルトン路チェック:", msg)
    if not ok:
        return

    real_counts = count_move_directions(path)
    total_moves = L ** 3 - 1

    print(f"restart_used = {restart_used}")
    print(f"総移動数 = {total_moves}")
    print(f"move_counts = {real_counts}")
    print(
        "move_rates  = "
        f"x:{real_counts['x']/total_moves:.3f}, "
        f"y:{real_counts['y']/total_moves:.3f}, "
        f"z:{real_counts['z']/total_moves:.3f}"
    )

    prime_points, prime_numbers, number_to_coord, coord_to_number = collect_prime_points(L, path)

    print(f"総点数 N = {L**3}")
    print(f"素数個数 = {len(prime_numbers)}")
    print(f"素数密度 = {len(prime_numbers) / (L**3):.4f}")

    plot_prime_3d_balanced(
        L,
        path,
        prime_points,
        save_path=f"images_balanced/figure_balanced_prime_lattice_L{L}.png",
        show_path=True,
    )

    analyze_diagonal_planes(L, coord_to_number)

    print("=" * 80)
    print("peak一致率 summary")
    print("L | mod | L%mod | match/total | rate")
    print("-" * 80)

    for mod_value in mod_values:
        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=10,
        )

        print(
            f"{L:2d} | "
            f"{mod_value:3d} | "
            f"{L % mod_value:5d} | "
            f"{match:3d}/{total:<3d} | "
            f"{rate:5.3f}"
        )

    # 代表として mod 7 の詳細を出す
    if 7 in mod_values:
        analyze_mod_residue_peaks_by_plane(L, coord_to_number, mod_value=7)


def run_balanced_sweep(
    L_values=(5, 8, 11, 12),
    mod_values=(3, 5, 7, 11),
    seed=42,
):
    print("=" * 100)
    print("Balanced path sweep")
    print("L | moves(x,y,z) | mod | L%mod | match/total | rate")
    print("-" * 100)

    for L in L_values:
        try:
            path, move_counts, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=500,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            print(f"L={L}: 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            print(f"L={L}: ハミルトン路NG: {msg}")
            continue

        _, _, _, coord_to_number = collect_prime_points(L, path)
        real_counts = count_move_directions(path)

        for mod_value in mod_values:
            match, total, rate = summarize_peak_match_rate(
                L,
                coord_to_number,
                mod_value=mod_value,
                min_candidates=10,
            )

            print(
                f"{L:2d} | "
                f"({real_counts['x']:4d},{real_counts['y']:4d},{real_counts['z']:4d}) | "
                f"{mod_value:3d} | "
                f"{L % mod_value:5d} | "
                f"{match:3d}/{total:<3d} | "
                f"{rate:5.3f}"
            )


def run_balanced_seed_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
):
    """
    seedを変えて、方向均衡ハミルトン路を複数生成し、
    peak_r == (s+1) % mod_value
    の一致率がどれくらい出るかを調べる。

    目的:
      Snake型では L % mod = 1 のとき rate=1.000 だった。
      方向均衡型でも同じ現象が出るか、
      それとも消えるかを seed 違いで確認する。
    """
    print("=" * 100)
    print("Balanced seed sweep")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seed_start={seed_start}, seed_count={seed_count}")
    print("-" * 100)
    print("seed | restart | moves(x,y,z) | balance_gap | match/total | rate")
    print("-" * 100)

    results = []
    failed_seeds = []

    for seed in range(seed_start, seed_start + seed_count):
        try:
            path, move_counts, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=max_restarts,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            failed_seeds.append(seed)
            print(f"{seed:4d} | 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            failed_seeds.append(seed)
            print(f"{seed:4d} | ハミルトン路NG: {msg}")
            continue

        real_counts = count_move_directions(path)
        balance_gap = max(real_counts.values()) - min(real_counts.values())

        _, _, _, coord_to_number = collect_prime_points(L, path)

        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        results.append({
            "seed": seed,
            "restart": restart_used,
            "x": real_counts["x"],
            "y": real_counts["y"],
            "z": real_counts["z"],
            "balance_gap": balance_gap,
            "match": match,
            "total": total,
            "rate": rate,
        })

        print(
            f"{seed:4d} | "
            f"{restart_used:7d} | "
            f"({real_counts['x']:4d},{real_counts['y']:4d},{real_counts['z']:4d}) | "
            f"{balance_gap:11d} | "
            f"{match:3d}/{total:<3d} | "
            f"{rate:5.3f}"
        )

    print()
    print("=" * 100)
    print("Balanced seed sweep summary")
    print("-" * 100)

    if not results:
        print("有効な結果がありません。")
        print(f"failed_seeds = {failed_seeds}")
        return

    rates = [r["rate"] for r in results]
    gaps = [r["balance_gap"] for r in results]

    avg_rate = sum(rates) / len(rates)
    min_rate = min(rates)
    max_rate = max(rates)

    avg_gap = sum(gaps) / len(gaps)
    min_gap = min(gaps)
    max_gap = max(gaps)

    zero_count = sum(1 for r in results if r["rate"] == 0.0)
    one_count = sum(1 for r in results if r["rate"] == 1.0)

    print(f"success_count = {len(results)}")
    print(f"failed_count  = {len(failed_seeds)}")
    print(f"failed_seeds  = {failed_seeds}")
    print()
    print(f"rate avg = {avg_rate:.3f}")
    print(f"rate min = {min_rate:.3f}")
    print(f"rate max = {max_rate:.3f}")
    print(f"rate == 0.000 count = {zero_count}")
    print(f"rate == 1.000 count = {one_count}")
    print()
    print(f"balance_gap avg = {avg_gap:.2f}")
    print(f"balance_gap min = {min_gap}")
    print(f"balance_gap max = {max_gap}")

    print()
    print("rate 上位")
    print("-" * 100)

    for r in sorted(results, key=lambda x: x["rate"], reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"restart={r['restart']:3d}, "
            f"moves=({r['x']},{r['y']},{r['z']}), "
            f"gap={r['balance_gap']}, "
            f"match={r['match']}/{r['total']}, "
            f"rate={r['rate']:.3f}"
        )

    print()
    print("rate 下位")
    print("-" * 100)

    for r in sorted(results, key=lambda x: x["rate"])[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"restart={r['restart']:3d}, "
            f"moves=({r['x']},{r['y']},{r['z']}), "
            f"gap={r['balance_gap']}, "
            f"match={r['match']}/{r['total']}, "
            f"rate={r['rate']:.3f}"
        )

def build_mod_residue_peak_rows(L, coord_to_number, mod_value=7):
    """
    各偶数 s=x+y+z 平面について、
    3以上の奇数 n の mod 分布を集計して、行データとして返す。

    既存の analyze_mod_residue_peaks_by_plane() は print 用。
    この関数は、保存・比較・可視化用。
    """
    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        if s % 2 != 0:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    # 3以上の奇数のみ対象
                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        counts = [0] * mod_value
        for n in nums:
            counts[n % mod_value] += 1

        cand = len(nums)
        peak_count = max(counts)
        peak_r = counts.index(peak_count)
        peak_rs = [r for r, c in enumerate(counts) if c == peak_count]

        peak_rate = peak_count / cand
        r0_count = counts[0]
        r0_rate = r0_count / cand
        expected_peak = (s + 1) % mod_value

        strict_match = (peak_r == expected_peak)
        tie_match = (expected_peak in peak_rs)

        rows.append({
            "s": s,
            "cand": cand,
            "counts": counts,
            "peak_r": peak_r,
            "peak_rs": peak_rs,
            "peak_count": peak_count,
            "peak_rate": peak_rate,
            "r0_count": r0_count,
            "r0_rate": r0_rate,
            "expected_peak": expected_peak,
            "strict_match": strict_match,
            "tie_match": tie_match,
        })

    return rows


def save_mod_residue_peak_table(
    save_path,
    L,
    seed,
    mod_value,
    move_counts,
    restart_used,
    match,
    total,
    rate,
    rows,
):
    """
    mod 剰余ピーク表を txt として保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("Balanced Hamiltonian detailed mod residue peak table\n")
        f.write("=" * 100 + "\n")
        f.write(f"L = {L}\n")
        f.write(f"seed = {seed}\n")
        f.write(f"mod = {mod_value}\n")
        f.write(f"L % mod = {L % mod_value}\n")
        f.write(f"restart_used = {restart_used}\n")
        f.write(f"move_counts = {move_counts}\n")
        f.write(f"match/total = {match}/{total}\n")
        f.write(f"rate = {rate:.3f}\n")
        f.write("\n")

        f.write("s | cand | peak_r | peak_rs | peak_count | peak_rate | r0_count | r0_rate | expected | strict | tie | counts\n")
        f.write("-" * 140 + "\n")

        for r in rows:
            f.write(
                f"{r['s']:2d} | "
                f"{r['cand']:4d} | "
                f"{r['peak_r']:6d} | "
                f"{str(r['peak_rs']):7s} | "
                f"{r['peak_count']:10d} | "
                f"{r['peak_rate']:9.3f} | "
                f"{r['r0_count']:8d} | "
                f"{r['r0_rate']:7.3f} | "
                f"{r['expected_peak']:8d} | "
                f"{'OK' if r['strict_match'] else '--':6s} | "
                f"{'OK' if r['tie_match'] else '--':3s} | "
                f"{r['counts']}\n"
            )

    print(f"保存しました: {save_path}")


def plot_mod_residue_heatmap(
    L,
    coord_to_number,
    mod_value=7,
    seed=None,
    save_path=None,
):
    """
    横軸: s = x+y+z
    縦軸: residue r
    色: その平面における n mod mod_value の個数

    expected_peak = (s+1) % mod_value も点で重ねる。
    """
    even_s_values = list(range(0, 3 * (L - 1) + 1, 2))

    # matrix[r][j] = s=even_s_values[j] における residue r の個数
    matrix = [[0 for _ in even_s_values] for _ in range(mod_value)]
    expected_points_x = []
    expected_points_y = []
    peak_points_x = []
    peak_points_y = []

    for j, s in enumerate(even_s_values):
        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        counts = [0] * mod_value
        for n in nums:
            counts[n % mod_value] += 1

        for r in range(mod_value):
            matrix[r][j] = counts[r]

        peak_r = counts.index(max(counts))
        expected_r = (s + 1) % mod_value

        peak_points_x.append(j)
        peak_points_y.append(peak_r)

        expected_points_x.append(j)
        expected_points_y.append(expected_r)

    fig = plt.figure(figsize=(11, 5))
    ax = fig.add_subplot(111)

    im = ax.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
    )

    ax.scatter(
        expected_points_x,
        expected_points_y,
        marker="x",
        s=55,
        label="expected: (s+1) mod m",
    )

    ax.scatter(
        peak_points_x,
        peak_points_y,
        marker="o",
        s=28,
        facecolors="none",
        label="actual peak residue",
    )

    title = f"Residue heatmap: L={L}, mod={mod_value}"
    if seed is not None:
        title += f", seed={seed}"

    ax.set_title(title)
    ax.set_xlabel("diagonal plane s = x+y+z")
    ax.set_ylabel(f"residue r mod {mod_value}")

    ax.set_xticks(range(len(even_s_values)))
    ax.set_xticklabels([str(s) for s in even_s_values])

    ax.set_yticks(range(mod_value))
    ax.set_yticklabels([str(r) for r in range(mod_value)])

    ax.legend(loc="upper right")
    fig.colorbar(im, ax=ax, label="count")

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=220, bbox_inches="tight")
        print(f"保存しました: {save_path}")

    plt.close(fig)


def run_balanced_seed_detail_compare(
    L=8,
    mod_value=7,
    seeds=(1, 34),
    max_restarts=500,
    min_candidates=10,
):
    """
    指定seedについて、方向均衡ハミルトン路を生成し、
    詳細な mod 剰余ピーク表と画像を保存する。

    保存内容:
      - 3D素数点画像
      - mod剰余ヒートマップ
      - 詳細な剰余ピーク表 txt
    """
    print("=" * 100)
    print("Balanced seed detail compare")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seeds={seeds}")
    print("=" * 100)

    for seed in seeds:
        print()
        print("-" * 100)
        print(f"seed={seed} detail")
        print("-" * 100)

        path, move_counts, restart_used = hamiltonian_balanced_greedy_3d(
            L=L,
            seed=seed,
            max_restarts=max_restarts,
            start=(0, 0, 0),
        )

        ok, msg = verify_hamiltonian_path(path, L)
        print("ハミルトン路チェック:", msg)
        if not ok:
            continue

        real_counts = count_move_directions(path)
        balance_gap = max(real_counts.values()) - min(real_counts.values())

        prime_points, prime_numbers, number_to_coord, coord_to_number = collect_prime_points(L, path)

        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        rate_text = f"{rate:.3f}".replace(".", "p")

        print(f"restart_used = {restart_used}")
        print(f"move_counts = {real_counts}")
        print(f"balance_gap = {balance_gap}")
        print(f"prime_count = {len(prime_numbers)}")
        print(f"match/total = {match}/{total}")
        print(f"rate = {rate:.3f}")

        rows = build_mod_residue_peak_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
        )

        # 3D素数点画像
        plot_prime_3d_balanced(
            L,
            path,
            prime_points,
            save_path=(
                f"images_balanced/"
                f"detail_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}_prime3d.png"
            ),
            show_path=True,
        )

        # mod剰余ヒートマップ
        plot_mod_residue_heatmap(
            L,
            coord_to_number,
            mod_value=mod_value,
            seed=seed,
            save_path=(
                f"images_balanced/"
                f"detail_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}_heatmap.png"
            ),
        )

        # 詳細表
        save_mod_residue_peak_table(
            save_path=(
                f"logs_balanced/"
                f"detail_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}.txt"
            ),
            L=L,
            seed=seed,
            mod_value=mod_value,
            move_counts=real_counts,
            restart_used=restart_used,
            match=match,
            total=total,
            rate=rate,
            rows=rows,
        )

def summarize_number_list(values):
    """
    数値リストの簡単な要約を返す。
    """
    if not values:
        return {
            "count": 0,
            "min": 0,
            "max": 0,
            "avg": 0.0,
        }

    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
    }


def build_direction_sequence(path):
    """
    path から移動方向列を作る。
    例: ["x", "x", "z", "y", ...]
    """
    dirs = []

    for a, b in zip(path[:-1], path[1:]):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        dz = abs(a[2] - b[2])

        if dx == 1:
            dirs.append("x")
        elif dy == 1:
            dirs.append("y")
        elif dz == 1:
            dirs.append("z")
        else:
            dirs.append("?")

    return dirs


def build_run_lengths(seq):
    """
    連続する同一値のラン長を返す。
    例: ["x","x","y","y","y","z"] -> [("x",2),("y",3),("z",1)]
    """
    if not seq:
        return []

    runs = []
    current = seq[0]
    length = 1

    for v in seq[1:]:
        if v == current:
            length += 1
        else:
            runs.append((current, length))
            current = v
            length = 1

    runs.append((current, length))
    return runs


def build_snake2d_order(L, y_reverse=False, first_x_reverse=False, reverse_whole=False):
    """
    2D Snake順序の候補を作る。

    y_reverse=False:
      y = 0,1,2,...,L-1
    y_reverse=True:
      y = L-1,...,1,0

    first_x_reverse=False:
      最初の行は x = 0,1,2,...
    first_x_reverse=True:
      最初の行は x = L-1,...,0

    reverse_whole=True:
      最後に全体順序を反転する。
    """
    order = []

    y_values = list(range(L))
    if y_reverse:
        y_values = list(reversed(y_values))

    for row_index, y in enumerate(y_values):
        reverse_x = first_x_reverse if row_index % 2 == 0 else not first_x_reverse

        x_values = list(range(L))
        if reverse_x:
            x_values = list(reversed(x_values))

        for x in x_values:
            order.append((x, y))

    if reverse_whole:
        order = list(reversed(order))

    return order


def spearman_like_rank_corr(rank_a, rank_b):
    """
    同じキー集合を持つ rank_a, rank_b の順位相関っぽい値を返す。
    1.0 に近いほど似ている。
    -1.0 に近いほど逆順に近い。

    厳密な統計用途ではなく、Snake類似度の簡易指標。
    """
    keys = list(rank_a.keys())
    n = len(keys)

    if n <= 1:
        return 1.0

    sum_d2 = 0
    for k in keys:
        d = rank_a[k] - rank_b[k]
        sum_d2 += d * d

    return 1.0 - (6.0 * sum_d2) / (n * (n * n - 1))


def calc_layer_snake_similarity(L, path):
    """
    各 z 層について、その層内で訪問された (x,y) の順番が
    2D Snake順序にどれくらい近いかを調べる。

    戻り値:
      layer_rows: 各z層の詳細
      summary: 全層の平均など
    """
    layer_points = {z: [] for z in range(L)}

    for coord in path:
        x, y, z = coord
        layer_points[z].append((x, y))

    # 2D Snake候補を複数作る
    snake_orders = []
    for y_reverse in (False, True):
        for first_x_reverse in (False, True):
            for reverse_whole in (False, True):
                order = build_snake2d_order(
                    L,
                    y_reverse=y_reverse,
                    first_x_reverse=first_x_reverse,
                    reverse_whole=reverse_whole,
                )
                snake_orders.append(order)

    snake_rank_candidates = []
    for order in snake_orders:
        snake_rank_candidates.append({p: i for i, p in enumerate(order)})

    layer_rows = []

    for z in range(L):
        pts = layer_points[z]

        # 実際の訪問順位
        actual_rank = {}
        for i, p in enumerate(pts):
            actual_rank[p] = i

        best_score = -999.0
        best_candidate_index = -1

        for ci, snake_rank in enumerate(snake_rank_candidates):
            score = spearman_like_rank_corr(actual_rank, snake_rank)
            if score > best_score:
                best_score = score
                best_candidate_index = ci

        layer_rows.append({
            "z": z,
            "points": len(pts),
            "best_snake_score": best_score,
            "best_candidate_index": best_candidate_index,
        })

    scores = [r["best_snake_score"] for r in layer_rows]

    summary = {
        "avg_snake_score": sum(scores) / len(scores) if scores else 0.0,
        "min_snake_score": min(scores) if scores else 0.0,
        "max_snake_score": max(scores) if scores else 0.0,
    }

    return layer_rows, summary


def analyze_single_path_structure(
    L,
    path,
    seed=None,
    restart_used=None,
    save_path=None,
):
    """
    1本のハミルトン路について、経路構造を解析する。

    見るもの:
      - x/y/z 移動回数
      - 方向連続ラン
      - z層滞在ラン
      - z層ごとの分断数
      - z層内訪問順序の 2D Snake 類似度
    """
    ok, msg = verify_hamiltonian_path(path, L)
    if not ok:
        raise ValueError(f"ハミルトン路NG: {msg}")

    move_counts = count_move_directions(path)
    total_moves = len(path) - 1
    balance_gap = max(move_counts.values()) - min(move_counts.values())

    dirs = build_direction_sequence(path)
    dir_runs = build_run_lengths(dirs)

    z_seq = [p[2] for p in path]
    z_runs = build_run_lengths(z_seq)

    # 方向別ラン長
    dir_run_lengths_by_axis = {"x": [], "y": [], "z": []}
    for d, length in dir_runs:
        if d in dir_run_lengths_by_axis:
            dir_run_lengths_by_axis[d].append(length)

    # z層ごとの分断数・最大滞在長
    layer_segment_count = {z: 0 for z in range(L)}
    layer_segment_lengths = {z: [] for z in range(L)}

    for z, length in z_runs:
        layer_segment_count[z] += 1
        layer_segment_lengths[z].append(length)

    layer_snake_rows, snake_summary = calc_layer_snake_similarity(L, path)

    # 出力用文字列を作る
    lines = []
    lines.append("=" * 100)
    lines.append("Hamiltonian path structure analysis")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    if seed is not None:
        lines.append(f"seed = {seed}")
    if restart_used is not None:
        lines.append(f"restart_used = {restart_used}")
    lines.append(f"hamiltonian_check = {msg}")
    lines.append("")
    lines.append("Move direction counts")
    lines.append("-" * 100)
    lines.append(f"total_moves = {total_moves}")
    lines.append(f"move_counts = {move_counts}")
    lines.append(
        "move_rates  = "
        f"x:{move_counts['x']/total_moves:.3f}, "
        f"y:{move_counts['y']/total_moves:.3f}, "
        f"z:{move_counts['z']/total_moves:.3f}"
    )
    lines.append(f"balance_gap = {balance_gap}")
    lines.append("")

    lines.append("Direction run length summary")
    lines.append("-" * 100)
    for axis in ("x", "y", "z"):
        summary = summarize_number_list(dir_run_lengths_by_axis[axis])
        lines.append(
            f"{axis}: "
            f"run_count={summary['count']}, "
            f"min={summary['min']}, "
            f"max={summary['max']}, "
            f"avg={summary['avg']:.2f}"
        )

    top_dir_runs = sorted(dir_runs, key=lambda x: x[1], reverse=True)[:15]
    lines.append("")
    lines.append("Top direction runs")
    lines.append("-" * 100)
    for d, length in top_dir_runs:
        lines.append(f"dir={d}, length={length}")

    lines.append("")
    lines.append("Z-layer run summary")
    lines.append("-" * 100)
    z_run_lengths = [length for _, length in z_runs]
    z_summary = summarize_number_list(z_run_lengths)
    lines.append(
        f"z_run_count={z_summary['count']}, "
        f"min={z_summary['min']}, "
        f"max={z_summary['max']}, "
        f"avg={z_summary['avg']:.2f}"
    )

    top_z_runs = sorted(z_runs, key=lambda x: x[1], reverse=True)[:15]
    lines.append("")
    lines.append("Top z-layer stays")
    lines.append("-" * 100)
    for z, length in top_z_runs:
        lines.append(f"z={z}, length={length}")

    lines.append("")
    lines.append("Layer fragmentation")
    lines.append("-" * 100)
    lines.append("z | segment_count | max_segment | avg_segment")
    lines.append("-" * 60)
    for z in range(L):
        segs = layer_segment_lengths[z]
        summary = summarize_number_list(segs)
        lines.append(
            f"{z:2d} | "
            f"{summary['count']:13d} | "
            f"{summary['max']:11d} | "
            f"{summary['avg']:11.2f}"
        )

    lines.append("")
    lines.append("2D Snake similarity inside each z-layer")
    lines.append("-" * 100)
    lines.append(
        f"avg_snake_score = {snake_summary['avg_snake_score']:.3f}, "
        f"min = {snake_summary['min_snake_score']:.3f}, "
        f"max = {snake_summary['max_snake_score']:.3f}"
    )
    lines.append("")
    lines.append("z | points | best_snake_score | candidate")
    lines.append("-" * 70)

    for r in layer_snake_rows:
        lines.append(
            f"{r['z']:2d} | "
            f"{r['points']:6d} | "
            f"{r['best_snake_score']:16.3f} | "
            f"{r['best_candidate_index']:9d}"
        )

    text = "\n".join(lines)

    print(text)

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"保存しました: {save_path}")

    return {
        "move_counts": move_counts,
        "balance_gap": balance_gap,
        "dir_runs": dir_runs,
        "z_runs": z_runs,
        "layer_snake_rows": layer_snake_rows,
        "snake_summary": snake_summary,
    }


def analyze_path_structure(
    L=8,
    seeds=(1, 34),
    mod_value=7,
    max_restarts=500,
):
    """
    seedごとの方向均衡ハミルトン路を生成し、
    経路構造を解析して txt に保存する。

    seed=1  : rate=0.000 の代表
    seed=34 : rate=0.875 の代表
    """
    print("=" * 100)
    print("Analyze path structure")
    print(f"L={L}, seeds={seeds}, mod={mod_value}")
    print("=" * 100)

    summary_rows = []

    for seed in seeds:
        path, move_counts, restart_used = hamiltonian_balanced_greedy_3d(
            L=L,
            seed=seed,
            max_restarts=max_restarts,
            start=(0, 0, 0),
        )

        _, _, _, coord_to_number = collect_prime_points(L, path)

        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=10,
        )

        rate_text = f"{rate:.3f}".replace(".", "p")

        result = analyze_single_path_structure(
            L=L,
            path=path,
            seed=seed,
            restart_used=restart_used,
            save_path=(
                f"logs_balanced/"
                f"path_structure_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}.txt"
            ),
        )

        summary_rows.append({
            "seed": seed,
            "restart": restart_used,
            "match": match,
            "total": total,
            "rate": rate,
            "move_counts": result["move_counts"],
            "balance_gap": result["balance_gap"],
            "avg_snake_score": result["snake_summary"]["avg_snake_score"],
            "min_snake_score": result["snake_summary"]["min_snake_score"],
            "max_snake_score": result["snake_summary"]["max_snake_score"],
        })

    print("")
    print("=" * 100)
    print("Path structure summary")
    print("=" * 100)
    print("seed | restart | match/total | rate | moves(x,y,z) | gap | avg_snake | min_snake | max_snake")
    print("-" * 120)

    for r in summary_rows:
        mc = r["move_counts"]
        print(
            f"{r['seed']:4d} | "
            f"{r['restart']:7d} | "
            f"{r['match']:3d}/{r['total']:<3d} | "
            f"{r['rate']:5.3f} | "
            f"({mc['x']:3d},{mc['y']:3d},{mc['z']:3d}) | "
            f"{r['balance_gap']:3d} | "
            f"{r['avg_snake_score']:9.3f} | "
            f"{r['min_snake_score']:9.3f} | "
            f"{r['max_snake_score']:9.3f}"
        )

def pearson_corr(xs, ys):
    """
    Pearson相関係数を返す。
    分散ゼロなどで計算不能な場合は None。
    """
    if len(xs) != len(ys) or len(xs) < 2:
        return None

    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)

    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]

    sx2 = sum(v * v for v in dx)
    sy2 = sum(v * v for v in dy)

    if sx2 == 0 or sy2 == 0:
        return None

    return sum(a * b for a, b in zip(dx, dy)) / math.sqrt(sx2 * sy2)


def rank_values(values):
    """
    Spearman相関用の順位を返す。
    同順位は平均順位にする。
    """
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)

    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1

        # 1始まり順位の平均
        avg_rank = (i + 1 + j + 1) / 2.0

        for k in range(i, j + 1):
            original_index = indexed[k][0]
            ranks[original_index] = avg_rank

        i = j + 1

    return ranks


def spearman_corr(xs, ys):
    """
    Spearman順位相関を返す。
    """
    if len(xs) != len(ys) or len(xs) < 2:
        return None

    rx = rank_values(xs)
    ry = rank_values(ys)

    return pearson_corr(rx, ry)


def calc_path_structure_metrics(L, path):
    """
    1本のハミルトン路から、相関分析用の構造指標を作る。

    主な指標:
      - z_run_count
      - max_z_stay
      - avg_z_stay
      - min_layer_segment_count
      - avg_layer_segment_count
      - max_layer_segment_count
      - max_layer_segment_len
      - z_block_score
      - avg_snake_score
    """
    move_counts = count_move_directions(path)
    total_moves = len(path) - 1
    balance_gap = max(move_counts.values()) - min(move_counts.values())

    dirs = build_direction_sequence(path)
    dir_runs = build_run_lengths(dirs)

    z_seq = [p[2] for p in path]
    z_runs = build_run_lengths(z_seq)

    # z層ごとの分断数・滞在長
    layer_segment_lengths = {z: [] for z in range(L)}

    for z, length in z_runs:
        layer_segment_lengths[z].append(length)

    layer_segment_counts = []
    layer_max_segments = []
    layer_avg_segments = []

    for z in range(L):
        segs = layer_segment_lengths[z]
        summary = summarize_number_list(segs)

        layer_segment_counts.append(summary["count"])
        layer_max_segments.append(summary["max"])
        layer_avg_segments.append(summary["avg"])

    z_run_lengths = [length for _, length in z_runs]
    z_summary = summarize_number_list(z_run_lengths)

    dir_run_lengths = [length for _, length in dir_runs]
    dir_summary = summarize_number_list(dir_run_lengths)

    # 方向別最大ラン
    dir_max = {"x": 0, "y": 0, "z": 0}
    for d, length in dir_runs:
        if d in dir_max:
            dir_max[d] = max(dir_max[d], length)

    # 層内Snake類似度
    _, snake_summary = calc_layer_snake_similarity(L, path)

    N = L ** 3

    # z_block_score:
    # 各z層の最大連続滞在長を足して全点数で割る。
    # 大きいほど「各層をまとまって訪問している」傾向。
    z_block_score = sum(layer_max_segments) / N if N > 0 else 0.0

    # z_fragment_score:
    # 層分断数の平均。大きいほど層を細切れに訪問。
    z_fragment_score = sum(layer_segment_counts) / len(layer_segment_counts)

    return {
        "move_x": move_counts["x"],
        "move_y": move_counts["y"],
        "move_z": move_counts["z"],
        "balance_gap": balance_gap,

        "dir_run_count": dir_summary["count"],
        "max_dir_run": dir_summary["max"],
        "avg_dir_run": dir_summary["avg"],
        "max_x_run": dir_max["x"],
        "max_y_run": dir_max["y"],
        "max_z_dir_run": dir_max["z"],

        "z_run_count": z_summary["count"],
        "max_z_stay": z_summary["max"],
        "avg_z_stay": z_summary["avg"],

        "min_layer_segment_count": min(layer_segment_counts),
        "avg_layer_segment_count": sum(layer_segment_counts) / len(layer_segment_counts),
        "max_layer_segment_count": max(layer_segment_counts),

        "min_layer_max_segment": min(layer_max_segments),
        "avg_layer_max_segment": sum(layer_max_segments) / len(layer_max_segments),
        "max_layer_segment_len": max(layer_max_segments),

        "min_layer_avg_segment": min(layer_avg_segments),
        "avg_layer_avg_segment": sum(layer_avg_segments) / len(layer_avg_segments),
        "max_layer_avg_segment": max(layer_avg_segments),

        "z_block_score": z_block_score,
        "z_fragment_score": z_fragment_score,

        "avg_snake_score": snake_summary["avg_snake_score"],
        "min_snake_score": snake_summary["min_snake_score"],
        "max_snake_score": snake_summary["max_snake_score"],
    }


def save_structure_correlation_csv(save_path, rows):
    """
    相関分析用の行データをCSVとして保存する。
    外部ライブラリなしで保存する。
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    headers = list(rows[0].keys())

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

        for row in rows:
            values = []
            for h in headers:
                v = row[h]
                if isinstance(v, float):
                    values.append(f"{v:.6f}")
                else:
                    values.append(str(v))
            f.write(",".join(values) + "\n")

    print(f"保存しました: {save_path}")


def save_structure_correlation_report(
    save_path,
    L,
    mod_value,
    seed_start,
    seed_count,
    rows,
    corr_rows,
):
    """
    相関分析のtxtレポートを保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    lines = []
    lines.append("=" * 100)
    lines.append("Structure correlation sweep report")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"seed_start = {seed_start}")
    lines.append(f"seed_count = {seed_count}")
    lines.append(f"success_count = {len(rows)}")
    lines.append("")

    lines.append("Correlation with rate")
    lines.append("-" * 100)
    lines.append("metric | pearson | spearman")
    lines.append("-" * 100)

    for c in corr_rows:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        lines.append(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    lines.append("")
    lines.append("Top rate rows")
    lines.append("-" * 100)
    lines.append("seed | rate | match/total | max_z_stay | z_block_score | avg_layer_segment_count | avg_snake_score")
    lines.append("-" * 100)

    for r in sorted(rows, key=lambda x: x["rate"], reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['rate']:.3f} | "
            f"{r['match']:3d}/{r['total']:<3d} | "
            f"{r['max_z_stay']:10d} | "
            f"{r['z_block_score']:.3f} | "
            f"{r['avg_layer_segment_count']:.2f} | "
            f"{r['avg_snake_score']:.3f}"
        )

    lines.append("")
    lines.append("Low rate rows")
    lines.append("-" * 100)
    lines.append("seed | rate | match/total | max_z_stay | z_block_score | avg_layer_segment_count | avg_snake_score")
    lines.append("-" * 100)

    for r in sorted(rows, key=lambda x: x["rate"])[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['rate']:.3f} | "
            f"{r['match']:3d}/{r['total']:<3d} | "
            f"{r['max_z_stay']:10d} | "
            f"{r['z_block_score']:.3f} | "
            f"{r['avg_layer_segment_count']:.2f} | "
            f"{r['avg_snake_score']:.3f}"
        )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def run_structure_correlation_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
):
    """
    seedを変えて方向均衡ハミルトン路を生成し、
    rate と経路構造指標の相関を見る。

    目的:
      seed=34 のような高rate経路が、
      z層ブロック性・層分断数・Snake類似度などと
      関係しているかを調べる。
    """
    print("=" * 100)
    print("Structure correlation sweep")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seed_start={seed_start}, seed_count={seed_count}")
    print("=" * 100)

    rows = []
    failed_seeds = []

    for seed in range(seed_start, seed_start + seed_count):
        try:
            path, _, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=max_restarts,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            failed_seeds.append(seed)
            print(f"seed={seed}: 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            failed_seeds.append(seed)
            print(f"seed={seed}: ハミルトン路NG: {msg}")
            continue

        _, _, _, coord_to_number = collect_prime_points(L, path)

        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        metrics = calc_path_structure_metrics(L, path)

        row = {
            "seed": seed,
            "restart": restart_used,
            "match": match,
            "total": total,
            "rate": rate,
        }
        row.update(metrics)

        rows.append(row)

        print(
            f"seed={seed:4d} | "
            f"rate={rate:.3f} | "
            f"match={match}/{total} | "
            f"max_z_stay={metrics['max_z_stay']:2d} | "
            f"z_block={metrics['z_block_score']:.3f} | "
            f"avg_seg_count={metrics['avg_layer_segment_count']:.2f} | "
            f"avg_snake={metrics['avg_snake_score']:.3f}"
        )

    print("")
    print("=" * 100)
    print("Structure correlation summary")
    print("=" * 100)
    print(f"success_count = {len(rows)}")
    print(f"failed_count  = {len(failed_seeds)}")
    print(f"failed_seeds  = {failed_seeds}")
    print("")

    if not rows:
        print("有効な結果がありません。")
        return

    rate_values = [r["rate"] for r in rows]

    metric_names = [
        "balance_gap",

        "dir_run_count",
        "max_dir_run",
        "avg_dir_run",
        "max_x_run",
        "max_y_run",
        "max_z_dir_run",

        "z_run_count",
        "max_z_stay",
        "avg_z_stay",

        "min_layer_segment_count",
        "avg_layer_segment_count",
        "max_layer_segment_count",

        "min_layer_max_segment",
        "avg_layer_max_segment",
        "max_layer_segment_len",

        "min_layer_avg_segment",
        "avg_layer_avg_segment",
        "max_layer_avg_segment",

        "z_block_score",
        "z_fragment_score",

        "avg_snake_score",
        "min_snake_score",
        "max_snake_score",
    ]

    corr_rows = []

    for metric in metric_names:
        xs = [r[metric] for r in rows]

        p = pearson_corr(xs, rate_values)
        s = spearman_corr(xs, rate_values)

        corr_rows.append({
            "metric": metric,
            "pearson": p,
            "spearman": s,
        })

    # 絶対値が大きい順で表示
    def corr_sort_key(c):
        vals = []
        if c["pearson"] is not None:
            vals.append(abs(c["pearson"]))
        if c["spearman"] is not None:
            vals.append(abs(c["spearman"]))
        return max(vals) if vals else 0.0

    corr_rows_sorted = sorted(corr_rows, key=corr_sort_key, reverse=True)

    print("Correlation with rate")
    print("-" * 100)
    print("metric | pearson | spearman")
    print("-" * 100)

    for c in corr_rows_sorted:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        print(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    print("")
    print("Top rate rows")
    print("-" * 100)

    for r in sorted(rows, key=lambda x: x["rate"], reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"rate={r['rate']:.3f}, "
            f"match={r['match']}/{r['total']}, "
            f"max_z_stay={r['max_z_stay']}, "
            f"z_block={r['z_block_score']:.3f}, "
            f"avg_seg_count={r['avg_layer_segment_count']:.2f}, "
            f"avg_snake={r['avg_snake_score']:.3f}"
        )

    print("")
    print("Low rate rows")
    print("-" * 100)

    for r in sorted(rows, key=lambda x: x["rate"])[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"rate={r['rate']:.3f}, "
            f"match={r['match']}/{r['total']}, "
            f"max_z_stay={r['max_z_stay']}, "
            f"z_block={r['z_block_score']:.3f}, "
            f"avg_seg_count={r['avg_layer_segment_count']:.2f}, "
            f"avg_snake={r['avg_snake_score']:.3f}"
        )

    save_structure_correlation_csv(
        save_path=(
            f"logs_balanced/"
            f"structure_correlation_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.csv"
        ),
        rows=rows,
    )

    save_structure_correlation_report(
        save_path=(
            f"logs_balanced/"
            f"structure_correlation_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.txt"
        ),
        L=L,
        mod_value=mod_value,
        seed_start=seed_start,
        seed_count=seed_count,
        rows=rows,
        corr_rows=corr_rows_sorted,
    )

def build_modular_alignment_rows(L, coord_to_number, mod_value=7):
    """
    各偶数 s = x+y+z 平面について、

        e = (n - (s + 1)) mod mod_value

    の分布を調べる。

    e=0 が多いほど、

        n ≡ s + 1 mod mod_value

    に近い。

    これは、peak_r = (s+1) mod m が出るかを
    直接見るための指標。
    """
    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        if s % 2 != 0:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    # 既存解析と同じく、3以上の奇数だけを見る
                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        alignment_counts = [0] * mod_value
        residue_counts = [0] * mod_value

        expected_r = (s + 1) % mod_value

        for n in nums:
            r = n % mod_value
            e = (n - (s + 1)) % mod_value

            residue_counts[r] += 1
            alignment_counts[e] += 1

        cand = len(nums)

        peak_e_count = max(alignment_counts)
        peak_e = alignment_counts.index(peak_e_count)
        peak_es = [e for e, c in enumerate(alignment_counts) if c == peak_e_count]

        e0_count = alignment_counts[0]
        e0_rate = e0_count / cand if cand > 0 else 0.0

        peak_r_count = max(residue_counts)
        peak_r = residue_counts.index(peak_r_count)

        strict_match = (peak_e == 0)
        tie_match = (0 in peak_es)

        rows.append({
            "s": s,
            "cand": cand,

            "expected_r": expected_r,

            "peak_r": peak_r,
            "peak_r_count": peak_r_count,

            "peak_e": peak_e,
            "peak_es": peak_es,
            "peak_e_count": peak_e_count,

            "e0_count": e0_count,
            "e0_rate": e0_rate,

            "strict_match": strict_match,
            "tie_match": tie_match,

            "alignment_counts": alignment_counts,
            "residue_counts": residue_counts,
        })

    return rows


def summarize_modular_alignment(rows, min_candidates=10):
    """
    build_modular_alignment_rows() の結果から、
    e=0 がピークになった平面の割合を集計する。
    """
    target_rows = [r for r in rows if r["cand"] >= min_candidates]

    total = len(target_rows)
    strict_match = sum(1 for r in target_rows if r["strict_match"])
    tie_match = sum(1 for r in target_rows if r["tie_match"])

    strict_rate = strict_match / total if total > 0 else 0.0
    tie_rate = tie_match / total if total > 0 else 0.0

    total_cand = sum(r["cand"] for r in target_rows)
    total_e0 = sum(r["e0_count"] for r in target_rows)

    global_e0_rate = total_e0 / total_cand if total_cand > 0 else 0.0

    # 平面ごとの e0_rate の平均
    avg_plane_e0_rate = (
        sum(r["e0_rate"] for r in target_rows) / total
        if total > 0
        else 0.0
    )

    return {
        "total": total,
        "strict_match": strict_match,
        "tie_match": tie_match,
        "strict_rate": strict_rate,
        "tie_rate": tie_rate,
        "total_cand": total_cand,
        "total_e0": total_e0,
        "global_e0_rate": global_e0_rate,
        "avg_plane_e0_rate": avg_plane_e0_rate,
    }


def save_modular_alignment_report(
    save_path,
    L,
    seed,
    mod_value,
    restart_used,
    move_counts,
    match,
    total,
    rate,
    rows,
    alignment_summary,
):
    """
    modular alignment の詳細レポートを txt 保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    lines = []
    lines.append("=" * 100)
    lines.append("Modular alignment analysis")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"seed = {seed}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"restart_used = {restart_used}")
    lines.append(f"move_counts = {move_counts}")
    lines.append("")
    lines.append("Peak match summary")
    lines.append("-" * 100)
    lines.append(f"peak_r match/total = {match}/{total}")
    lines.append(f"peak_r rate = {rate:.3f}")
    lines.append("")
    lines.append("Alignment summary")
    lines.append("-" * 100)
    lines.append(f"alignment strict_match/total = {alignment_summary['strict_match']}/{alignment_summary['total']}")
    lines.append(f"alignment strict_rate = {alignment_summary['strict_rate']:.3f}")
    lines.append(f"alignment tie_match/total = {alignment_summary['tie_match']}/{alignment_summary['total']}")
    lines.append(f"alignment tie_rate = {alignment_summary['tie_rate']:.3f}")
    lines.append(f"global_e0_rate = {alignment_summary['global_e0_rate']:.3f}")
    lines.append(f"avg_plane_e0_rate = {alignment_summary['avg_plane_e0_rate']:.3f}")
    lines.append("")
    lines.append("Formula")
    lines.append("-" * 100)
    lines.append("e = (n - (x+y+z+1)) mod m")
    lines.append("On plane s=x+y+z, this becomes e = (n - (s+1)) mod m.")
    lines.append("If e=0 is dominant, then n ≡ s+1 mod m is dominant.")
    lines.append("")
    lines.append("Per-plane details")
    lines.append("-" * 160)
    lines.append(
        "s | cand | expected_r | peak_r | peak_e | peak_es | "
        "e0_count | e0_rate | strict | tie | alignment_counts | residue_counts"
    )
    lines.append("-" * 160)

    for r in rows:
        lines.append(
            f"{r['s']:2d} | "
            f"{r['cand']:4d} | "
            f"{r['expected_r']:10d} | "
            f"{r['peak_r']:6d} | "
            f"{r['peak_e']:6d} | "
            f"{str(r['peak_es']):7s} | "
            f"{r['e0_count']:8d} | "
            f"{r['e0_rate']:7.3f} | "
            f"{'OK' if r['strict_match'] else '--':6s} | "
            f"{'OK' if r['tie_match'] else '--':3s} | "
            f"{r['alignment_counts']} | "
            f"{r['residue_counts']}"
        )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def plot_modular_alignment_heatmap(
    L,
    coord_to_number,
    mod_value=7,
    seed=None,
    save_path=None,
):
    """
    横軸: s = x+y+z
    縦軸: e = (n - (s+1)) mod m
    色: count

    e=0 の行に数が集まるほど、
    n ≡ s+1 mod m の合同整列が強い。
    """
    even_s_values = list(range(0, 3 * (L - 1) + 1, 2))

    matrix = [[0 for _ in even_s_values] for _ in range(mod_value)]

    peak_points_x = []
    peak_points_y = []

    for j, s in enumerate(even_s_values):
        counts = [0] * mod_value

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    if n >= 3 and n % 2 == 1:
                        e = (n - (s + 1)) % mod_value
                        counts[e] += 1

        for e in range(mod_value):
            matrix[e][j] = counts[e]

        if sum(counts) > 0:
            peak_e = counts.index(max(counts))
            peak_points_x.append(j)
            peak_points_y.append(peak_e)

    fig = plt.figure(figsize=(11, 5))
    ax = fig.add_subplot(111)

    im = ax.imshow(
        matrix,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
    )

    # e=0 の基準線
    ax.axhline(
        y=0,
        linestyle="--",
        linewidth=1.2,
        label="target alignment e=0",
    )

    # 実際のピーク e
    ax.scatter(
        peak_points_x,
        peak_points_y,
        marker="o",
        s=35,
        facecolors="none",
        label="actual peak e",
    )

    title = f"Modular alignment heatmap: L={L}, mod={mod_value}"
    if seed is not None:
        title += f", seed={seed}"

    ax.set_title(title)
    ax.set_xlabel("diagonal plane s = x+y+z")
    ax.set_ylabel(f"alignment error e mod {mod_value}")

    ax.set_xticks(range(len(even_s_values)))
    ax.set_xticklabels([str(s) for s in even_s_values])

    ax.set_yticks(range(mod_value))
    ax.set_yticklabels([str(e) for e in range(mod_value)])

    ax.legend(loc="upper right")
    fig.colorbar(im, ax=ax, label="count")

    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=220, bbox_inches="tight")
        print(f"保存しました: {save_path}")

    plt.close(fig)


def run_modular_alignment_analysis(
    L=8,
    mod_value=7,
    seeds=(1, 34),
    max_restarts=500,
    min_candidates=10,
):
    """
    指定seedについて modular alignment を解析する。

    見る式:

        e = (n - (x+y+z+1)) mod m

    e=0 が各斜め平面でピークになれば、
    peak_r = (s+1) mod m が出る。

    seed=1 と seed=34 の差を見るための関数。
    """
    print("=" * 100)
    print("Run modular alignment analysis")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seeds={seeds}")
    print("=" * 100)

    summary_rows = []

    for seed in seeds:
        print("")
        print("-" * 100)
        print(f"seed={seed}")
        print("-" * 100)

        path, _, restart_used = hamiltonian_balanced_greedy_3d(
            L=L,
            seed=seed,
            max_restarts=max_restarts,
            start=(0, 0, 0),
        )

        ok, msg = verify_hamiltonian_path(path, L)
        print("ハミルトン路チェック:", msg)
        if not ok:
            continue

        move_counts = count_move_directions(path)

        _, _, _, coord_to_number = collect_prime_points(L, path)

        match, total, rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        rows = build_modular_alignment_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
        )

        alignment_summary = summarize_modular_alignment(
            rows,
            min_candidates=min_candidates,
        )

        rate_text = f"{rate:.3f}".replace(".", "p")

        print(f"restart_used = {restart_used}")
        print(f"move_counts = {move_counts}")
        print(f"peak_r match/total = {match}/{total}")
        print(f"peak_r rate = {rate:.3f}")
        print(f"alignment strict_rate = {alignment_summary['strict_rate']:.3f}")
        print(f"alignment tie_rate = {alignment_summary['tie_rate']:.3f}")
        print(f"global_e0_rate = {alignment_summary['global_e0_rate']:.3f}")
        print(f"avg_plane_e0_rate = {alignment_summary['avg_plane_e0_rate']:.3f}")

        plot_modular_alignment_heatmap(
            L,
            coord_to_number,
            mod_value=mod_value,
            seed=seed,
            save_path=(
                f"images_balanced/"
                f"alignment_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}.png"
            ),
        )

        save_modular_alignment_report(
            save_path=(
                f"logs_balanced/"
                f"alignment_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}.txt"
            ),
            L=L,
            seed=seed,
            mod_value=mod_value,
            restart_used=restart_used,
            move_counts=move_counts,
            match=match,
            total=total,
            rate=rate,
            rows=rows,
            alignment_summary=alignment_summary,
        )

        summary_rows.append({
            "seed": seed,
            "restart": restart_used,
            "match": match,
            "total": total,
            "rate": rate,
            "alignment_strict_rate": alignment_summary["strict_rate"],
            "alignment_tie_rate": alignment_summary["tie_rate"],
            "global_e0_rate": alignment_summary["global_e0_rate"],
            "avg_plane_e0_rate": alignment_summary["avg_plane_e0_rate"],
        })

    print("")
    print("=" * 100)
    print("Modular alignment summary")
    print("=" * 100)
    print(
        "seed | restart | peak_match | peak_rate | "
        "align_strict | align_tie | global_e0 | avg_plane_e0"
    )
    print("-" * 120)

    for r in summary_rows:
        print(
            f"{r['seed']:4d} | "
            f"{r['restart']:7d} | "
            f"{r['match']:3d}/{r['total']:<3d} | "
            f"{r['rate']:9.3f} | "
            f"{r['alignment_strict_rate']:12.3f} | "
            f"{r['alignment_tie_rate']:9.3f} | "
            f"{r['global_e0_rate']:9.3f} | "
            f"{r['avg_plane_e0_rate']:12.3f}"
        )

def save_modular_alignment_sweep_csv(save_path, rows):
    """
    modular alignment sweep の結果をCSV保存する。
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    headers = list(rows[0].keys())

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

        for row in rows:
            values = []
            for h in headers:
                v = row[h]
                if isinstance(v, float):
                    values.append(f"{v:.6f}")
                else:
                    values.append(str(v))
            f.write(",".join(values) + "\n")

    print(f"保存しました: {save_path}")


def save_modular_alignment_sweep_report(
    save_path,
    L,
    mod_value,
    seed_start,
    seed_count,
    rows,
    corr_rows,
):
    """
    modular alignment sweep の集計レポートを txt 保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    baseline = 1.0 / mod_value

    lines = []
    lines.append("=" * 100)
    lines.append("Modular alignment sweep report")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"seed_start = {seed_start}")
    lines.append(f"seed_count = {seed_count}")
    lines.append(f"success_count = {len(rows)}")
    lines.append(f"random_baseline = 1/mod = {baseline:.6f}")
    lines.append("")
    lines.append("Meaning")
    lines.append("-" * 100)
    lines.append("e = (n - (x+y+z+1)) mod m")
    lines.append("global_e0_rate measures how often e=0 occurs over target planes.")
    lines.append("If global_e0_rate is much larger than 1/m, the path is aligned with n ≡ x+y+z+1 mod m.")
    lines.append("")
    lines.append("Correlation with peak_rate")
    lines.append("-" * 100)
    lines.append("metric | pearson | spearman")
    lines.append("-" * 100)

    for c in corr_rows:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        lines.append(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    lines.append("")
    lines.append("Top peak_rate rows")
    lines.append("-" * 120)
    lines.append(
        "seed | peak_rate | peak_match | align_strict | global_e0 | e0_lift | e0_ratio | avg_plane_e0"
    )
    lines.append("-" * 120)

    for r in sorted(rows, key=lambda x: x["peak_rate"], reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['alignment_strict_rate']:.3f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_lift']:.3f} | "
            f"{r['e0_ratio']:.3f} | "
            f"{r['avg_plane_e0_rate']:.3f}"
        )

    lines.append("")
    lines.append("Low peak_rate rows")
    lines.append("-" * 120)
    lines.append(
        "seed | peak_rate | peak_match | align_strict | global_e0 | e0_lift | e0_ratio | avg_plane_e0"
    )
    lines.append("-" * 120)

    for r in sorted(rows, key=lambda x: x["peak_rate"])[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['alignment_strict_rate']:.3f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_lift']:.3f} | "
            f"{r['e0_ratio']:.3f} | "
            f"{r['avg_plane_e0_rate']:.3f}"
        )

    lines.append("")
    lines.append("Top global_e0_rate rows")
    lines.append("-" * 120)
    lines.append(
        "seed | global_e0 | peak_rate | peak_match | e0_lift | e0_ratio | avg_plane_e0"
    )
    lines.append("-" * 120)

    for r in sorted(rows, key=lambda x: x["global_e0_rate"], reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['e0_lift']:.3f} | "
            f"{r['e0_ratio']:.3f} | "
            f"{r['avg_plane_e0_rate']:.3f}"
        )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def run_modular_alignment_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
):
    """
    seedを変えて、modular alignment を一括解析する。

    見る式:
        e = (n - (x+y+z+1)) mod m

    目的:
      peak_rate が高い経路ほど、
      global_e0_rate や avg_plane_e0_rate が高いかを見る。

    注意:
      alignment_strict_rate は peak_rate とほぼ同じ意味になる。
      より重要なのは global_e0_rate / avg_plane_e0_rate / e0_lift。
    """
    print("=" * 100)
    print("Modular alignment sweep")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seed_start={seed_start}, seed_count={seed_count}")
    print("=" * 100)

    baseline = 1.0 / mod_value

    rows = []
    failed_seeds = []

    for seed in range(seed_start, seed_start + seed_count):
        try:
            path, _, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=max_restarts,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            failed_seeds.append(seed)
            print(f"seed={seed}: 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            failed_seeds.append(seed)
            print(f"seed={seed}: ハミルトン路NG: {msg}")
            continue

        move_counts = count_move_directions(path)

        _, _, _, coord_to_number = collect_prime_points(L, path)

        peak_match, peak_total, peak_rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        alignment_rows = build_modular_alignment_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
        )

        alignment_summary = summarize_modular_alignment(
            alignment_rows,
            min_candidates=min_candidates,
        )

        global_e0_rate = alignment_summary["global_e0_rate"]
        avg_plane_e0_rate = alignment_summary["avg_plane_e0_rate"]

        e0_lift = global_e0_rate - baseline
        e0_ratio = global_e0_rate / baseline if baseline > 0 else 0.0

        row = {
            "seed": seed,
            "restart": restart_used,

            "move_x": move_counts["x"],
            "move_y": move_counts["y"],
            "move_z": move_counts["z"],

            "peak_match": peak_match,
            "peak_total": peak_total,
            "peak_rate": peak_rate,

            "alignment_strict_match": alignment_summary["strict_match"],
            "alignment_total": alignment_summary["total"],
            "alignment_strict_rate": alignment_summary["strict_rate"],

            "alignment_tie_match": alignment_summary["tie_match"],
            "alignment_tie_rate": alignment_summary["tie_rate"],

            "total_cand": alignment_summary["total_cand"],
            "total_e0": alignment_summary["total_e0"],
            "global_e0_rate": global_e0_rate,
            "avg_plane_e0_rate": avg_plane_e0_rate,

            "random_baseline": baseline,
            "e0_lift": e0_lift,
            "e0_ratio": e0_ratio,
        }

        rows.append(row)

        print(
            f"seed={seed:4d} | "
            f"peak_rate={peak_rate:.3f} | "
            f"match={peak_match}/{peak_total} | "
            f"align={alignment_summary['strict_rate']:.3f} | "
            f"global_e0={global_e0_rate:.3f} | "
            f"e0_lift={e0_lift:+.3f} | "
            f"e0_ratio={e0_ratio:.3f}"
        )

    print("")
    print("=" * 100)
    print("Modular alignment sweep summary")
    print("=" * 100)
    print(f"success_count = {len(rows)}")
    print(f"failed_count  = {len(failed_seeds)}")
    print(f"failed_seeds  = {failed_seeds}")
    print(f"random_baseline = 1/{mod_value} = {baseline:.6f}")
    print("")

    if not rows:
        print("有効な結果がありません。")
        return

    peak_rates = [r["peak_rate"] for r in rows]

    metric_names = [
        "alignment_strict_rate",
        "alignment_tie_rate",
        "global_e0_rate",
        "avg_plane_e0_rate",
        "e0_lift",
        "e0_ratio",
        "total_e0",
        "total_cand",
    ]

    corr_rows = []

    for metric in metric_names:
        xs = [r[metric] for r in rows]

        p = pearson_corr(xs, peak_rates)
        s = spearman_corr(xs, peak_rates)

        corr_rows.append({
            "metric": metric,
            "pearson": p,
            "spearman": s,
        })

    def corr_sort_key(c):
        vals = []
        if c["pearson"] is not None:
            vals.append(abs(c["pearson"]))
        if c["spearman"] is not None:
            vals.append(abs(c["spearman"]))
        return max(vals) if vals else 0.0

    corr_rows_sorted = sorted(corr_rows, key=corr_sort_key, reverse=True)

    print("Correlation with peak_rate")
    print("-" * 100)
    print("metric | pearson | spearman")
    print("-" * 100)

    for c in corr_rows_sorted:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        print(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    print("")
    print("Top peak_rate rows")
    print("-" * 100)

    for r in sorted(rows, key=lambda x: x["peak_rate"], reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"global_e0={r['global_e0_rate']:.3f}, "
            f"e0_lift={r['e0_lift']:+.3f}, "
            f"e0_ratio={r['e0_ratio']:.3f}, "
            f"avg_plane_e0={r['avg_plane_e0_rate']:.3f}"
        )

    print("")
    print("Low peak_rate rows")
    print("-" * 100)

    for r in sorted(rows, key=lambda x: x["peak_rate"])[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"global_e0={r['global_e0_rate']:.3f}, "
            f"e0_lift={r['e0_lift']:+.3f}, "
            f"e0_ratio={r['e0_ratio']:.3f}, "
            f"avg_plane_e0={r['avg_plane_e0_rate']:.3f}"
        )

    print("")
    print("Top global_e0_rate rows")
    print("-" * 100)

    for r in sorted(rows, key=lambda x: x["global_e0_rate"], reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"global_e0={r['global_e0_rate']:.3f}, "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"e0_lift={r['e0_lift']:+.3f}, "
            f"e0_ratio={r['e0_ratio']:.3f}, "
            f"avg_plane_e0={r['avg_plane_e0_rate']:.3f}"
        )

    csv_path = (
        f"logs_balanced/"
        f"modular_alignment_sweep_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.csv"
    )

    txt_path = (
        f"logs_balanced/"
        f"modular_alignment_sweep_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.txt"
    )

    save_modular_alignment_sweep_csv(csv_path, rows)

    save_modular_alignment_sweep_report(
        save_path=txt_path,
        L=L,
        mod_value=mod_value,
        seed_start=seed_start,
        seed_count=seed_count,
        rows=rows,
        corr_rows=corr_rows_sorted,
    )
def calc_alignment_plane_outlier_rows(L, coord_to_number, mod_value=7, min_candidates=10):
    """
    各 s=x+y+z 平面について、
    e = (n - (s+1)) mod m の分布を調べ、
    e=0 がどれくらい強いかを詳細化する。

    見るポイント:
      - e=0 がピークか
      - e=0 が唯一ピークか
      - e=0 が何位か
      - e=0 と最大ピークとの差
      - e=0 と2番手との差
    """
    base_rows = build_modular_alignment_rows(
        L,
        coord_to_number,
        mod_value=mod_value,
    )

    out_rows = []

    for r in base_rows:
        counts = r["alignment_counts"]
        cand = r["cand"]

        e0_count = counts[0]
        peak_count = max(counts)

        # e=0 より大きい個数を持つ residue が何種類あるか
        greater_counts = sorted(
            set(c for c in counts if c > e0_count),
            reverse=True
        )
        e0_rank = 1 + len(greater_counts)

        # e=0 が最大値に並んでいるか
        e0_is_peak_or_tied = (e0_count == peak_count)

        # e=0 が唯一ピークか
        e0_is_unique_peak = (
            e0_count == peak_count and counts.count(peak_count) == 1
        )

        # e=0 と最大ピークとの差
        # 0なら e=0 は少なくとも同率ピーク
        e0_gap_to_peak = e0_count - peak_count

        # e=0 と、e=0以外の最大値との差
        other_counts = counts[1:]
        best_other = max(other_counts) if other_counts else 0
        e0_margin_over_best_other = e0_count - best_other

        # e=0 が惜しい場合
        # 例: e=0 が2位で、ピークとの差が1〜2程度
        near_miss = (
            (not e0_is_peak_or_tied)
            and e0_rank == 2
            and abs(e0_gap_to_peak) <= 2
        )

        target_used = cand >= min_candidates

        out = dict(r)
        out.update({
            "target_used": target_used,

            "e0_rank": e0_rank,
            "e0_is_peak_or_tied": e0_is_peak_or_tied,
            "e0_is_unique_peak": e0_is_unique_peak,
            "e0_gap_to_peak": e0_gap_to_peak,
            "best_other": best_other,
            "e0_margin_over_best_other": e0_margin_over_best_other,
            "near_miss": near_miss,

            "peak_e_count": peak_count,
            "peak_e_rate": peak_count / cand if cand > 0 else 0.0,
        })

        out_rows.append(out)

    return out_rows


def save_alignment_outlier_compare_csv(save_path, rows):
    """
    outlier compare の平面別データをCSV保存する。
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    headers = [
        "seed",
        "restart",
        "peak_rate",
        "global_e0_rate",
        "e0_lift",
        "e0_ratio",

        "s",
        "cand",
        "expected_r",

        "peak_r",
        "peak_e",
        "peak_e_count",
        "peak_e_rate",

        "e0_count",
        "e0_rate",
        "e0_rank",
        "e0_is_peak_or_tied",
        "e0_is_unique_peak",
        "e0_gap_to_peak",
        "best_other",
        "e0_margin_over_best_other",
        "near_miss",

        "target_used",
        "alignment_counts",
        "residue_counts",
    ]

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

        for row in rows:
            values = []
            for h in headers:
                v = row.get(h, "")
                if isinstance(v, float):
                    values.append(f"{v:.6f}")
                else:
                    # listをCSVに入れるのでカンマを壊さないようにする
                    text = str(v).replace(",", ";")
                    values.append(text)

            f.write(",".join(values) + "\n")

    print(f"保存しました: {save_path}")


def save_alignment_outlier_compare_report(
    save_path,
    L,
    mod_value,
    seeds,
    summary_rows,
    plane_rows,
):
    """
    outlier compare のtxtレポートを保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    baseline = 1.0 / mod_value

    lines = []
    lines.append("=" * 100)
    lines.append("Alignment outlier compare report")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"seeds = {seeds}")
    lines.append(f"random_baseline = 1/mod = {baseline:.6f}")
    lines.append("")
    lines.append("Meaning")
    lines.append("-" * 100)
    lines.append("e = (n - (x+y+z+1)) mod m")
    lines.append("If e=0 is locally dominant on many s-planes, peak_r ≡ s+1 mod m appears.")
    lines.append("global_e0_rate can be high even when e=0 is not locally dominant on each plane.")
    lines.append("")

    lines.append("Seed summary")
    lines.append("-" * 130)
    lines.append(
        "seed | restart | peak_rate | peak_match | align_rate | global_e0 | "
        "e0_lift | e0_ratio | unique_peak | tied_peak | near_miss | avg_e0_rank"
    )
    lines.append("-" * 130)

    for r in summary_rows:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['restart']:7d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['alignment_strict_rate']:.3f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_lift']:+.3f} | "
            f"{r['e0_ratio']:.3f} | "
            f"{r['unique_peak_count']:11d} | "
            f"{r['tied_peak_count']:9d} | "
            f"{r['near_miss_count']:9d} | "
            f"{r['avg_e0_rank']:.2f}"
        )

    lines.append("")
    lines.append("Per-seed plane details")
    lines.append("=" * 160)

    for seed in seeds:
        rows = [r for r in plane_rows if r["seed"] == seed]

        seed_summary = next((r for r in summary_rows if r["seed"] == seed), None)
        if seed_summary is None:
            continue

        lines.append("")
        lines.append("-" * 160)
        lines.append(
            f"seed={seed}, "
            f"peak_rate={seed_summary['peak_rate']:.3f}, "
            f"global_e0={seed_summary['global_e0_rate']:.3f}, "
            f"e0_ratio={seed_summary['e0_ratio']:.3f}"
        )
        lines.append("-" * 160)
        lines.append(
            "s | cand | exp_r | peak_r | peak_e | e0_count | e0_rate | "
            "e0_rank | unique | tied | gap_to_peak | margin_other | near | counts"
        )
        lines.append("-" * 160)

        for r in rows:
            # min_candidates未満も参考表示するが、印をつける
            mark = "*" if r["target_used"] else " "

            lines.append(
                f"{mark}{r['s']:2d} | "
                f"{r['cand']:4d} | "
                f"{r['expected_r']:5d} | "
                f"{r['peak_r']:6d} | "
                f"{r['peak_e']:6d} | "
                f"{r['e0_count']:8d} | "
                f"{r['e0_rate']:7.3f} | "
                f"{r['e0_rank']:7d} | "
                f"{'Y' if r['e0_is_unique_peak'] else 'N':6s} | "
                f"{'Y' if r['e0_is_peak_or_tied'] else 'N':4s} | "
                f"{r['e0_gap_to_peak']:11d} | "
                f"{r['e0_margin_over_best_other']:12d} | "
                f"{'Y' if r['near_miss'] else 'N':4s} | "
                f"{r['alignment_counts']}"
            )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def run_alignment_outlier_compare(
    L=8,
    mod_value=7,
    seeds=(34, 29, 47, 1, 14),
    max_restarts=500,
    min_candidates=10,
    save_heatmaps=True,
):
    """
    modular alignment の外れ値を比較する。

    比較したい代表:
      - seed=34: global_e0 高い / peak_rate 高い
      - seed=29: global_e0 高い / peak_rate 低い
      - seed=47: global_e0 高い / peak_rate 低い
      - seed=1 : global_e0 ほぼ基準 / peak_rate 低い
      - seed=14: global_e0 低め / peak_rate 低い

    目的:
      global_e0_rate が高くても peak_rate が低い場合、
      e=0 が各平面でピークになっているのか、
      それとも全体では多いが各平面では2位以下なのかを調べる。
    """
    print("=" * 100)
    print("Alignment outlier compare")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seeds={seeds}")
    print("=" * 100)

    baseline = 1.0 / mod_value

    summary_rows = []
    all_plane_rows = []

    for seed in seeds:
        print("")
        print("-" * 100)
        print(f"seed={seed}")
        print("-" * 100)

        path, _, restart_used = hamiltonian_balanced_greedy_3d(
            L=L,
            seed=seed,
            max_restarts=max_restarts,
            start=(0, 0, 0),
        )

        ok, msg = verify_hamiltonian_path(path, L)
        print("ハミルトン路チェック:", msg)
        if not ok:
            continue

        _, _, _, coord_to_number = collect_prime_points(L, path)

        peak_match, peak_total, peak_rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        alignment_rows = build_modular_alignment_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
        )

        alignment_summary = summarize_modular_alignment(
            alignment_rows,
            min_candidates=min_candidates,
        )

        detail_rows = calc_alignment_plane_outlier_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        target_rows = [r for r in detail_rows if r["target_used"]]

        unique_peak_count = sum(1 for r in target_rows if r["e0_is_unique_peak"])
        tied_peak_count = sum(1 for r in target_rows if r["e0_is_peak_or_tied"])
        near_miss_count = sum(1 for r in target_rows if r["near_miss"])

        avg_e0_rank = (
            sum(r["e0_rank"] for r in target_rows) / len(target_rows)
            if target_rows
            else 0.0
        )

        avg_gap_to_peak = (
            sum(r["e0_gap_to_peak"] for r in target_rows) / len(target_rows)
            if target_rows
            else 0.0
        )

        global_e0_rate = alignment_summary["global_e0_rate"]
        e0_lift = global_e0_rate - baseline
        e0_ratio = global_e0_rate / baseline if baseline > 0 else 0.0

        summary = {
            "seed": seed,
            "restart": restart_used,

            "peak_match": peak_match,
            "peak_total": peak_total,
            "peak_rate": peak_rate,

            "alignment_strict_rate": alignment_summary["strict_rate"],
            "alignment_tie_rate": alignment_summary["tie_rate"],

            "global_e0_rate": global_e0_rate,
            "avg_plane_e0_rate": alignment_summary["avg_plane_e0_rate"],
            "e0_lift": e0_lift,
            "e0_ratio": e0_ratio,

            "unique_peak_count": unique_peak_count,
            "tied_peak_count": tied_peak_count,
            "near_miss_count": near_miss_count,
            "avg_e0_rank": avg_e0_rank,
            "avg_gap_to_peak": avg_gap_to_peak,
        }

        summary_rows.append(summary)

        for r in detail_rows:
            row = dict(r)
            row.update({
                "seed": seed,
                "restart": restart_used,
                "peak_rate": peak_rate,
                "global_e0_rate": global_e0_rate,
                "e0_lift": e0_lift,
                "e0_ratio": e0_ratio,
            })
            all_plane_rows.append(row)

        print(f"restart_used = {restart_used}")
        print(f"peak_match = {peak_match}/{peak_total}")
        print(f"peak_rate = {peak_rate:.3f}")
        print(f"alignment_strict_rate = {alignment_summary['strict_rate']:.3f}")
        print(f"global_e0_rate = {global_e0_rate:.3f}")
        print(f"e0_lift = {e0_lift:+.3f}")
        print(f"e0_ratio = {e0_ratio:.3f}")
        print(f"unique_peak_count = {unique_peak_count}")
        print(f"tied_peak_count = {tied_peak_count}")
        print(f"near_miss_count = {near_miss_count}")
        print(f"avg_e0_rank = {avg_e0_rank:.2f}")
        print(f"avg_gap_to_peak = {avg_gap_to_peak:.2f}")

        if save_heatmaps:
            rate_text = f"{peak_rate:.3f}".replace(".", "p")
            plot_modular_alignment_heatmap(
                L,
                coord_to_number,
                mod_value=mod_value,
                seed=seed,
                save_path=(
                    f"images_balanced/"
                    f"outlier_alignment_L{L}_mod{mod_value}_seed{seed:03d}_rate{rate_text}.png"
                ),
            )

    print("")
    print("=" * 100)
    print("Alignment outlier summary")
    print("=" * 100)
    print(
        "seed | peak_rate | peak_match | global_e0 | e0_ratio | "
        "unique | tied | near | avg_rank | avg_gap"
    )
    print("-" * 120)

    for r in summary_rows:
        print(
            f"{r['seed']:4d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_ratio']:.3f} | "
            f"{r['unique_peak_count']:6d} | "
            f"{r['tied_peak_count']:4d} | "
            f"{r['near_miss_count']:4d} | "
            f"{r['avg_e0_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f}"
        )

    seed_text = "_".join(str(s) for s in seeds)

    csv_path = (
        f"logs_balanced/"
        f"alignment_outlier_compare_L{L}_mod{mod_value}_seeds_{seed_text}.csv"
    )

    txt_path = (
        f"logs_balanced/"
        f"alignment_outlier_compare_L{L}_mod{mod_value}_seeds_{seed_text}.txt"
    )

    save_alignment_outlier_compare_csv(
        save_path=csv_path,
        rows=all_plane_rows,
    )

    save_alignment_outlier_compare_report(
        save_path=txt_path,
        L=L,
        mod_value=mod_value,
        seeds=seeds,
        summary_rows=summary_rows,
        plane_rows=all_plane_rows,
    )

def save_local_dominance_sweep_csv(save_path, rows):
    """
    local dominance sweep の結果をCSV保存する。
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    headers = list(rows[0].keys())

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

        for row in rows:
            values = []
            for h in headers:
                v = row[h]
                if isinstance(v, float):
                    values.append(f"{v:.6f}")
                else:
                    values.append(str(v))
            f.write(",".join(values) + "\n")

    print(f"保存しました: {save_path}")


def save_local_dominance_sweep_report(
    save_path,
    L,
    mod_value,
    seed_start,
    seed_count,
    rows,
    corr_rows,
):
    """
    local dominance sweep のtxtレポートを保存する。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    baseline = 1.0 / mod_value

    lines = []
    lines.append("=" * 100)
    lines.append("Local dominance sweep report")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"seed_start = {seed_start}")
    lines.append(f"seed_count = {seed_count}")
    lines.append(f"success_count = {len(rows)}")
    lines.append(f"random_baseline = 1/mod = {baseline:.6f}")
    lines.append("")
    lines.append("Meaning")
    lines.append("-" * 100)
    lines.append("e = (n - (x+y+z+1)) mod m")
    lines.append("global_e0_rate measures global alignment.")
    lines.append("unique_peak_rate measures how often e=0 is the unique local peak on each s-plane.")
    lines.append("tied_peak_rate measures how often e=0 is included in the local peak set.")
    lines.append("avg_e0_rank near 1 means e=0 is usually near the top.")
    lines.append("avg_gap_to_peak near 0 means e=0 is close to the local maximum.")
    lines.append("")

    lines.append("Correlation with current peak_rate")
    lines.append("-" * 100)
    lines.append("metric | pearson | spearman")
    lines.append("-" * 100)

    for c in corr_rows:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        lines.append(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    lines.append("")
    lines.append("Top peak_rate rows")
    lines.append("-" * 140)
    lines.append(
        "seed | peak_rate | peak_match | unique_rate | tied_rate | near_rate | "
        "avg_rank | avg_gap | global_e0 | e0_ratio"
    )
    lines.append("-" * 140)

    for r in sorted(rows, key=lambda x: x["peak_rate"], reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['unique_peak_rate']:.3f} | "
            f"{r['tied_peak_rate']:.3f} | "
            f"{r['near_miss_rate']:.3f} | "
            f"{r['avg_e0_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_ratio']:.3f}"
        )

    lines.append("")
    lines.append("Top unique_peak_rate rows")
    lines.append("-" * 140)
    lines.append(
        "seed | unique_rate | peak_rate | peak_match | tied_rate | avg_rank | "
        "avg_gap | global_e0 | e0_ratio"
    )
    lines.append("-" * 140)

    for r in sorted(rows, key=lambda x: (x["unique_peak_rate"], x["peak_rate"]), reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['unique_peak_rate']:.3f} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['tied_peak_rate']:.3f} | "
            f"{r['avg_e0_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_ratio']:.3f}"
        )

    lines.append("")
    lines.append("Top tied_peak_rate rows")
    lines.append("-" * 140)
    lines.append(
        "seed | tied_rate | peak_rate | peak_match | unique_rate | avg_rank | "
        "avg_gap | global_e0 | e0_ratio"
    )
    lines.append("-" * 140)

    for r in sorted(rows, key=lambda x: (x["tied_peak_rate"], x["peak_rate"]), reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['tied_peak_rate']:.3f} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['unique_peak_rate']:.3f} | "
            f"{r['avg_e0_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_ratio']:.3f}"
        )

    lines.append("")
    lines.append("Low peak_rate rows")
    lines.append("-" * 140)
    lines.append(
        "seed | peak_rate | peak_match | unique_rate | tied_rate | near_rate | "
        "avg_rank | avg_gap | global_e0 | e0_ratio"
    )
    lines.append("-" * 140)

    for r in sorted(rows, key=lambda x: x["peak_rate"])[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['peak_rate']:.3f} | "
            f"{r['peak_match']:3d}/{r['peak_total']:<3d} | "
            f"{r['unique_peak_rate']:.3f} | "
            f"{r['tied_peak_rate']:.3f} | "
            f"{r['near_miss_rate']:.3f} | "
            f"{r['avg_e0_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['global_e0_rate']:.3f} | "
            f"{r['e0_ratio']:.3f}"
        )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def run_local_dominance_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
):
    """
    seedを変えて、各斜め平面ごとの e=0 の局所優勢を解析する。

    見る式:
        e = (n - (x+y+z+1)) mod m

    目的:
      peak_rate は global_e0_rate だけでは説明しきれない。
      そこで、各 s=x+y+z 平面ごとに e=0 が
      単独ピーク・同率ピーク・何位・ピーク差どれくらいかを調べる。

    主な指標:
      - unique_peak_count / unique_peak_rate
      - tied_peak_count / tied_peak_rate
      - near_miss_count / near_miss_rate
      - avg_e0_rank
      - avg_gap_to_peak
      - avg_margin_over_best_other
    """
    print("=" * 100)
    print("Local dominance sweep")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seed_start={seed_start}, seed_count={seed_count}")
    print("=" * 100)

    baseline = 1.0 / mod_value

    rows = []
    failed_seeds = []

    for seed in range(seed_start, seed_start + seed_count):
        try:
            path, _, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=max_restarts,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            failed_seeds.append(seed)
            print(f"seed={seed}: 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            failed_seeds.append(seed)
            print(f"seed={seed}: ハミルトン路NG: {msg}")
            continue

        move_counts = count_move_directions(path)

        _, _, _, coord_to_number = collect_prime_points(L, path)

        peak_match, peak_total, peak_rate = summarize_peak_match_rate(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        alignment_rows = build_modular_alignment_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
        )

        alignment_summary = summarize_modular_alignment(
            alignment_rows,
            min_candidates=min_candidates,
        )

        detail_rows = calc_alignment_plane_outlier_rows(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        target_rows = [r for r in detail_rows if r["target_used"]]
        target_total = len(target_rows)

        unique_peak_count = sum(1 for r in target_rows if r["e0_is_unique_peak"])
        tied_peak_count = sum(1 for r in target_rows if r["e0_is_peak_or_tied"])
        near_miss_count = sum(1 for r in target_rows if r["near_miss"])

        unique_peak_rate = unique_peak_count / target_total if target_total > 0 else 0.0
        tied_peak_rate = tied_peak_count / target_total if target_total > 0 else 0.0
        near_miss_rate = near_miss_count / target_total if target_total > 0 else 0.0

        avg_e0_rank = (
            sum(r["e0_rank"] for r in target_rows) / target_total
            if target_total > 0
            else 0.0
        )

        avg_gap_to_peak = (
            sum(r["e0_gap_to_peak"] for r in target_rows) / target_total
            if target_total > 0
            else 0.0
        )

        avg_margin_over_best_other = (
            sum(r["e0_margin_over_best_other"] for r in target_rows) / target_total
            if target_total > 0
            else 0.0
        )

        avg_e0_rate = (
            sum(r["e0_rate"] for r in target_rows) / target_total
            if target_total > 0
            else 0.0
        )

        # 正の局所優勢だけを足す。
        # e=0 が他の residue よりどれくらい勝っているかを見る簡易スコア。
        positive_margin_sum = sum(
            max(0, r["e0_margin_over_best_other"])
            for r in target_rows
        )

        positive_margin_avg = (
            positive_margin_sum / target_total
            if target_total > 0
            else 0.0
        )

        global_e0_rate = alignment_summary["global_e0_rate"]
        avg_plane_e0_rate = alignment_summary["avg_plane_e0_rate"]
        e0_lift = global_e0_rate - baseline
        e0_ratio = global_e0_rate / baseline if baseline > 0 else 0.0

        row = {
            "seed": seed,
            "restart": restart_used,

            "move_x": move_counts["x"],
            "move_y": move_counts["y"],
            "move_z": move_counts["z"],

            "peak_match": peak_match,
            "peak_total": peak_total,
            "peak_rate": peak_rate,

            "alignment_strict_rate": alignment_summary["strict_rate"],
            "alignment_tie_rate": alignment_summary["tie_rate"],

            "target_total": target_total,

            "unique_peak_count": unique_peak_count,
            "tied_peak_count": tied_peak_count,
            "near_miss_count": near_miss_count,

            "unique_peak_rate": unique_peak_rate,
            "tied_peak_rate": tied_peak_rate,
            "near_miss_rate": near_miss_rate,

            "avg_e0_rank": avg_e0_rank,
            "avg_gap_to_peak": avg_gap_to_peak,
            "avg_margin_over_best_other": avg_margin_over_best_other,
            "positive_margin_sum": positive_margin_sum,
            "positive_margin_avg": positive_margin_avg,

            "global_e0_rate": global_e0_rate,
            "avg_plane_e0_rate": avg_plane_e0_rate,
            "avg_e0_rate": avg_e0_rate,

            "random_baseline": baseline,
            "e0_lift": e0_lift,
            "e0_ratio": e0_ratio,
        }

        rows.append(row)

        print(
            f"seed={seed:4d} | "
            f"peak_rate={peak_rate:.3f} | "
            f"match={peak_match}/{peak_total} | "
            f"unique={unique_peak_count}/{target_total}({unique_peak_rate:.3f}) | "
            f"tied={tied_peak_count}/{target_total}({tied_peak_rate:.3f}) | "
            f"avg_rank={avg_e0_rank:.2f} | "
            f"avg_gap={avg_gap_to_peak:.2f} | "
            f"global_e0={global_e0_rate:.3f}"
        )

    print("")
    print("=" * 100)
    print("Local dominance sweep summary")
    print("=" * 100)
    print(f"success_count = {len(rows)}")
    print(f"failed_count  = {len(failed_seeds)}")
    print(f"failed_seeds  = {failed_seeds}")
    print(f"random_baseline = 1/{mod_value} = {baseline:.6f}")
    print("")

    if not rows:
        print("有効な結果がありません。")
        return

    peak_rates = [r["peak_rate"] for r in rows]

    metric_names = [
        # 局所優勢系
        "unique_peak_count",
        "tied_peak_count",
        "near_miss_count",

        "unique_peak_rate",
        "tied_peak_rate",
        "near_miss_rate",

        "avg_e0_rank",
        "avg_gap_to_peak",
        "avg_margin_over_best_other",
        "positive_margin_sum",
        "positive_margin_avg",

        # 全体整列系
        "global_e0_rate",
        "avg_plane_e0_rate",
        "avg_e0_rate",
        "e0_lift",
        "e0_ratio",

        # 参考
        "alignment_strict_rate",
        "alignment_tie_rate",
    ]

    corr_rows = []

    for metric in metric_names:
        xs = [r[metric] for r in rows]

        p = pearson_corr(xs, peak_rates)
        s = spearman_corr(xs, peak_rates)

        corr_rows.append({
            "metric": metric,
            "pearson": p,
            "spearman": s,
        })

    def corr_sort_key(c):
        vals = []
        if c["pearson"] is not None:
            vals.append(abs(c["pearson"]))
        if c["spearman"] is not None:
            vals.append(abs(c["spearman"]))
        return max(vals) if vals else 0.0

    corr_rows_sorted = sorted(corr_rows, key=corr_sort_key, reverse=True)

    print("Correlation with current peak_rate")
    print("-" * 100)
    print("metric | pearson | spearman")
    print("-" * 100)

    for c in corr_rows_sorted:
        p = c["pearson"]
        s = c["spearman"]

        p_text = "None" if p is None else f"{p:.3f}"
        s_text = "None" if s is None else f"{s:.3f}"

        print(f"{c['metric']} | {p_text:>7s} | {s_text:>8s}")

    print("")
    print("Top peak_rate rows")
    print("-" * 120)

    for r in sorted(rows, key=lambda x: x["peak_rate"], reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"unique={r['unique_peak_count']}/{r['target_total']}({r['unique_peak_rate']:.3f}), "
            f"tied={r['tied_peak_count']}/{r['target_total']}({r['tied_peak_rate']:.3f}), "
            f"avg_rank={r['avg_e0_rank']:.2f}, "
            f"avg_gap={r['avg_gap_to_peak']:.2f}, "
            f"global_e0={r['global_e0_rate']:.3f}"
        )

    print("")
    print("Top unique_peak_rate rows")
    print("-" * 120)

    for r in sorted(rows, key=lambda x: (x["unique_peak_rate"], x["peak_rate"]), reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"unique={r['unique_peak_count']}/{r['target_total']}({r['unique_peak_rate']:.3f}), "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"tied={r['tied_peak_rate']:.3f}, "
            f"avg_rank={r['avg_e0_rank']:.2f}, "
            f"avg_gap={r['avg_gap_to_peak']:.2f}, "
            f"global_e0={r['global_e0_rate']:.3f}"
        )

    print("")
    print("Top tied_peak_rate rows")
    print("-" * 120)

    for r in sorted(rows, key=lambda x: (x["tied_peak_rate"], x["peak_rate"]), reverse=True)[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"tied={r['tied_peak_count']}/{r['target_total']}({r['tied_peak_rate']:.3f}), "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"unique={r['unique_peak_rate']:.3f}, "
            f"avg_rank={r['avg_e0_rank']:.2f}, "
            f"avg_gap={r['avg_gap_to_peak']:.2f}, "
            f"global_e0={r['global_e0_rate']:.3f}"
        )

    print("")
    print("Low peak_rate rows")
    print("-" * 120)

    for r in sorted(rows, key=lambda x: x["peak_rate"])[:10]:
        print(
            f"seed={r['seed']:4d}, "
            f"peak_rate={r['peak_rate']:.3f}, "
            f"match={r['peak_match']}/{r['peak_total']}, "
            f"unique={r['unique_peak_count']}/{r['target_total']}({r['unique_peak_rate']:.3f}), "
            f"tied={r['tied_peak_count']}/{r['target_total']}({r['tied_peak_rate']:.3f}), "
            f"avg_rank={r['avg_e0_rank']:.2f}, "
            f"avg_gap={r['avg_gap_to_peak']:.2f}, "
            f"global_e0={r['global_e0_rate']:.3f}"
        )

    csv_path = (
        f"logs_balanced/"
        f"local_dominance_sweep_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.csv"
    )

    txt_path = (
        f"logs_balanced/"
        f"local_dominance_sweep_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.txt"
    )

    save_local_dominance_sweep_csv(
        save_path=csv_path,
        rows=rows,
    )

    save_local_dominance_sweep_report(
        save_path=txt_path,
        L=L,
        mod_value=mod_value,
        seed_start=seed_start,
        seed_count=seed_count,
        rows=rows,
        corr_rows=corr_rows_sorted,
    )

def build_peak_rate_3way_rows(L, coord_to_number, mod_value=7):
    """
    各 s=x+y+z 平面について、
    peak_rate を3種類で判定するための行データを作る。

    current:
      既存方式。
      counts.index(max_count) が expected_r と一致するか。

    strict:
      expected_r が単独ピークか。

    tie-aware:
      expected_r が同率ピーク集合に含まれるか。

    解析対象:
      既存解析と同じく、
      s は偶数平面のみ、
      n は 3以上の奇数のみ。
    """
    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        if s % 2 != 0:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        counts = [0] * mod_value

        for n in nums:
            counts[n % mod_value] += 1

        cand = len(nums)

        expected_r = (s + 1) % mod_value

        max_count = max(counts)

        # 既存方式: 最初に見つかった最大値の residue を採用
        current_peak_r = counts.index(max_count)

        # 同率ピークを全部集める
        peak_rs = [r for r, c in enumerate(counts) if c == max_count]

        expected_count = counts[expected_r]

        current_match = (current_peak_r == expected_r)

        # expected_r が単独ピーク
        strict_match = (
            expected_count == max_count
            and counts.count(max_count) == 1
        )

        # expected_r が同率ピーク集合に含まれる
        tie_match = (expected_r in peak_rs)

        # expected_r の順位
        # 例: expected_count より大きい値が1種類なら2位
        greater_values = sorted(
            set(c for c in counts if c > expected_count),
            reverse=True
        )
        expected_rank = 1 + len(greater_values)

        # expected_r と最大ピークとの差
        # 0なら同率以上、負なら足りない
        gap_to_peak = expected_count - max_count

        # expected_r と expected_r以外の最大値との差
        other_counts = [counts[r] for r in range(mod_value) if r != expected_r]
        best_other = max(other_counts) if other_counts else 0
        margin_over_best_other = expected_count - best_other

        rows.append({
            "s": s,
            "cand": cand,
            "counts": counts,

            "expected_r": expected_r,
            "expected_count": expected_count,

            "current_peak_r": current_peak_r,
            "peak_rs": peak_rs,
            "max_count": max_count,

            "current_match": current_match,
            "strict_match": strict_match,
            "tie_match": tie_match,

            "expected_rank": expected_rank,
            "gap_to_peak": gap_to_peak,
            "best_other": best_other,
            "margin_over_best_other": margin_over_best_other,

            "expected_rate": expected_count / cand if cand > 0 else 0.0,
            "max_rate": max_count / cand if cand > 0 else 0.0,
        })

    return rows


def summarize_peak_rate_3way(
    L,
    coord_to_number,
    mod_value=7,
    min_candidates=10,
):
    """
    peak_rate を3種類で集計する。

    current_peak_rate:
      既存方式 counts.index(max) による一致率。

    strict_peak_rate:
      expected_r = (s+1) mod m が単独ピークの割合。

    tie_peak_rate:
      expected_r = (s+1) mod m が同率ピークに含まれる割合。
    """
    rows = build_peak_rate_3way_rows(
        L,
        coord_to_number,
        mod_value=mod_value,
    )

    target_rows = [r for r in rows if r["cand"] >= min_candidates]

    total = len(target_rows)

    current_match = sum(1 for r in target_rows if r["current_match"])
    strict_match = sum(1 for r in target_rows if r["strict_match"])
    tie_match = sum(1 for r in target_rows if r["tie_match"])

    current_rate = current_match / total if total > 0 else 0.0
    strict_rate = strict_match / total if total > 0 else 0.0
    tie_rate = tie_match / total if total > 0 else 0.0

    avg_expected_rank = (
        sum(r["expected_rank"] for r in target_rows) / total
        if total > 0
        else 0.0
    )

    avg_gap_to_peak = (
        sum(r["gap_to_peak"] for r in target_rows) / total
        if total > 0
        else 0.0
    )

    avg_margin_over_best_other = (
        sum(r["margin_over_best_other"] for r in target_rows) / total
        if total > 0
        else 0.0
    )

    avg_expected_rate = (
        sum(r["expected_rate"] for r in target_rows) / total
        if total > 0
        else 0.0
    )

    return {
        "total": total,

        "current_match": current_match,
        "strict_match": strict_match,
        "tie_match": tie_match,

        "current_rate": current_rate,
        "strict_rate": strict_rate,
        "tie_rate": tie_rate,

        "avg_expected_rank": avg_expected_rank,
        "avg_gap_to_peak": avg_gap_to_peak,
        "avg_margin_over_best_other": avg_margin_over_best_other,
        "avg_expected_rate": avg_expected_rate,

        "rows": rows,
        "target_rows": target_rows,
    }


def save_peak_rate_3way_csv(save_path, rows):
    """
    peak_rate 3way sweep のCSV保存。
    """
    if not rows:
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    headers = list(rows[0].keys())

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")

        for row in rows:
            values = []

            for h in headers:
                v = row[h]

                if isinstance(v, float):
                    values.append(f"{v:.6f}")
                else:
                    values.append(str(v))

            f.write(",".join(values) + "\n")

    print(f"保存しました: {save_path}")


def save_peak_rate_3way_report(
    save_path,
    L,
    mod_value,
    seed_start,
    seed_count,
    rows,
):
    """
    peak_rate 3way sweep のtxtレポート保存。
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    lines = []
    lines.append("=" * 100)
    lines.append("Peak rate 3-way sweep report")
    lines.append("=" * 100)
    lines.append(f"L = {L}")
    lines.append(f"mod = {mod_value}")
    lines.append(f"L % mod = {L % mod_value}")
    lines.append(f"seed_start = {seed_start}")
    lines.append(f"seed_count = {seed_count}")
    lines.append(f"success_count = {len(rows)}")
    lines.append("")
    lines.append("Definitions")
    lines.append("-" * 100)
    lines.append("expected_r = (s+1) mod m")
    lines.append("current_peak_rate : existing behavior; counts.index(max_count) == expected_r")
    lines.append("strict_peak_rate  : expected_r is the unique peak")
    lines.append("tie_peak_rate     : expected_r is included in the peak residue set")
    lines.append("")

    if rows:
        avg_current = sum(r["current_rate"] for r in rows) / len(rows)
        avg_strict = sum(r["strict_rate"] for r in rows) / len(rows)
        avg_tie = sum(r["tie_rate"] for r in rows) / len(rows)

        lines.append("Average rates")
        lines.append("-" * 100)
        lines.append(f"avg_current_rate = {avg_current:.3f}")
        lines.append(f"avg_strict_rate  = {avg_strict:.3f}")
        lines.append(f"avg_tie_rate     = {avg_tie:.3f}")
        lines.append("")

    lines.append("Top current_rate rows")
    lines.append("-" * 140)
    lines.append(
        "seed | current | strict | tie | current_match | strict_match | tie_match | "
        "avg_rank | avg_gap | avg_margin"
    )
    lines.append("-" * 140)

    for r in sorted(rows, key=lambda x: x["current_rate"], reverse=True)[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['current_rate']:.3f} | "
            f"{r['strict_rate']:.3f} | "
            f"{r['tie_rate']:.3f} | "
            f"{r['current_match']:3d}/{r['total']:<3d} | "
            f"{r['strict_match']:3d}/{r['total']:<3d} | "
            f"{r['tie_match']:3d}/{r['total']:<3d} | "
            f"{r['avg_expected_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['avg_margin_over_best_other']:.2f}"
        )

    lines.append("")
    lines.append("Rows where tie_rate is high but current_rate is low")
    lines.append("-" * 140)
    lines.append(
        "seed | current | strict | tie | current_match | strict_match | tie_match | "
        "avg_rank | avg_gap | avg_margin"
    )
    lines.append("-" * 140)

    # 同率ピークに含まれているのに current で低く見えるものを見る
    for r in sorted(
        rows,
        key=lambda x: (x["tie_rate"] - x["current_rate"], x["tie_rate"]),
        reverse=True,
    )[:15]:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['current_rate']:.3f} | "
            f"{r['strict_rate']:.3f} | "
            f"{r['tie_rate']:.3f} | "
            f"{r['current_match']:3d}/{r['total']:<3d} | "
            f"{r['strict_match']:3d}/{r['total']:<3d} | "
            f"{r['tie_match']:3d}/{r['total']:<3d} | "
            f"{r['avg_expected_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['avg_margin_over_best_other']:.2f}"
        )

    lines.append("")
    lines.append("All rows")
    lines.append("-" * 140)
    lines.append(
        "seed | current | strict | tie | current_match | strict_match | tie_match | "
        "avg_rank | avg_gap | avg_margin"
    )
    lines.append("-" * 140)

    for r in rows:
        lines.append(
            f"{r['seed']:4d} | "
            f"{r['current_rate']:.3f} | "
            f"{r['strict_rate']:.3f} | "
            f"{r['tie_rate']:.3f} | "
            f"{r['current_match']:3d}/{r['total']:<3d} | "
            f"{r['strict_match']:3d}/{r['total']:<3d} | "
            f"{r['tie_match']:3d}/{r['total']:<3d} | "
            f"{r['avg_expected_rank']:.2f} | "
            f"{r['avg_gap_to_peak']:.2f} | "
            f"{r['avg_margin_over_best_other']:.2f}"
        )

    text = "\n".join(lines)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"保存しました: {save_path}")
    print(text)


def run_peak_rate_3way_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
):
    """
    peak_rate を3種類で整理して seed sweep する。

    current_peak_rate:
      既存の counts.index(max) による一致率。

    strict_peak_rate:
      expected_r が単独ピークの割合。

    tie_peak_rate:
      expected_r が同率ピークに含まれる割合。

    目的:
      同率ピークにより current_peak_rate が低く見えるケースを分離する。
    """
    print("=" * 100)
    print("Peak rate 3-way sweep")
    print(f"L={L}, mod={mod_value}, L%mod={L % mod_value}")
    print(f"seed_start={seed_start}, seed_count={seed_count}")
    print("=" * 100)
    print(
        "seed | current | strict | tie | "
        "current_match | strict_match | tie_match | avg_rank | avg_gap"
    )
    print("-" * 120)

    rows = []
    failed_seeds = []

    for seed in range(seed_start, seed_start + seed_count):
        try:
            path, _, restart_used = hamiltonian_balanced_greedy_3d(
                L=L,
                seed=seed,
                max_restarts=max_restarts,
                start=(0, 0, 0),
            )
        except RuntimeError as e:
            failed_seeds.append(seed)
            print(f"seed={seed}: 生成失敗: {e}")
            continue

        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            failed_seeds.append(seed)
            print(f"seed={seed}: ハミルトン路NG: {msg}")
            continue

        _, _, _, coord_to_number = collect_prime_points(L, path)

        summary = summarize_peak_rate_3way(
            L,
            coord_to_number,
            mod_value=mod_value,
            min_candidates=min_candidates,
        )

        row = {
            "seed": seed,
            "restart": restart_used,

            "total": summary["total"],

            "current_match": summary["current_match"],
            "strict_match": summary["strict_match"],
            "tie_match": summary["tie_match"],

            "current_rate": summary["current_rate"],
            "strict_rate": summary["strict_rate"],
            "tie_rate": summary["tie_rate"],

            "avg_expected_rank": summary["avg_expected_rank"],
            "avg_gap_to_peak": summary["avg_gap_to_peak"],
            "avg_margin_over_best_other": summary["avg_margin_over_best_other"],
            "avg_expected_rate": summary["avg_expected_rate"],
        }

        rows.append(row)

        print(
            f"{seed:4d} | "
            f"{row['current_rate']:.3f} | "
            f"{row['strict_rate']:.3f} | "
            f"{row['tie_rate']:.3f} | "
            f"{row['current_match']:3d}/{row['total']:<3d} | "
            f"{row['strict_match']:3d}/{row['total']:<3d} | "
            f"{row['tie_match']:3d}/{row['total']:<3d} | "
            f"{row['avg_expected_rank']:.2f} | "
            f"{row['avg_gap_to_peak']:.2f}"
        )

    print("")
    print("=" * 100)
    print("Peak rate 3-way summary")
    print("=" * 100)
    print(f"success_count = {len(rows)}")
    print(f"failed_count  = {len(failed_seeds)}")
    print(f"failed_seeds  = {failed_seeds}")
    print("")

    if not rows:
        print("有効な結果がありません。")
        return

    avg_current = sum(r["current_rate"] for r in rows) / len(rows)
    avg_strict = sum(r["strict_rate"] for r in rows) / len(rows)
    avg_tie = sum(r["tie_rate"] for r in rows) / len(rows)

    print(f"avg_current_rate = {avg_current:.3f}")
    print(f"avg_strict_rate  = {avg_strict:.3f}")
    print(f"avg_tie_rate     = {avg_tie:.3f}")

    print("")
    print("tie_rate - current_rate が大きいseed")
    print("-" * 120)

    for r in sorted(
        rows,
        key=lambda x: (x["tie_rate"] - x["current_rate"], x["tie_rate"]),
        reverse=True,
    )[:10]:
        diff = r["tie_rate"] - r["current_rate"]
        print(
            f"seed={r['seed']:4d}, "
            f"current={r['current_rate']:.3f}, "
            f"strict={r['strict_rate']:.3f}, "
            f"tie={r['tie_rate']:.3f}, "
            f"diff={diff:.3f}, "
            f"current={r['current_match']}/{r['total']}, "
            f"strict={r['strict_match']}/{r['total']}, "
            f"tie={r['tie_match']}/{r['total']}, "
            f"avg_rank={r['avg_expected_rank']:.2f}"
        )

    csv_path = (
        f"logs_balanced/"
        f"peak_rate_3way_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.csv"
    )

    txt_path = (
        f"logs_balanced/"
        f"peak_rate_3way_L{L}_mod{mod_value}_seeds{seed_start}_{seed_start + seed_count - 1}.txt"
    )

    save_peak_rate_3way_csv(csv_path, rows)

    save_peak_rate_3way_report(
        save_path=txt_path,
        L=L,
        mod_value=mod_value,
        seed_start=seed_start,
        seed_count=seed_count,
        rows=rows,
    )

    plot_peak_rate_3way_histogram(
        rows,
        L=L,
        mod_value=mod_value,
        save_path=f"images_balanced/peak_rate_3way_hist_L{L}_mod{mod_value}.png",
    )    

def plot_peak_rate_3way_histogram(
    rows,
    L=8,
    mod_value=7,
    save_path="images_balanced/peak_rate_3way_hist_L8_mod7.png",
):
    """
    current / strict / tie の peak_rate 分布を棒グラフで保存する。

    rows は run_peak_rate_3way_sweep() 内で作っている rows を想定。
    各 row には以下が含まれる想定:
      - current_rate
      - strict_rate
      - tie_rate
    """
    if not rows:
        print("plot_peak_rate_3way_histogram: rows が空です")
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # L=8, mod=7 では対象平面 total=8 なので、
    # rate は 0/8, 1/8, ..., 8/8 の離散値になる。
    bins = [i / 8 for i in range(9)]

    current_counts = {v: 0 for v in bins}
    strict_counts = {v: 0 for v in bins}
    tie_counts = {v: 0 for v in bins}

    def round_rate(v):
        # 浮動小数誤差対策
        return round(v * 8) / 8

    for r in rows:
        current_counts[round_rate(r["current_rate"])] += 1
        strict_counts[round_rate(r["strict_rate"])] += 1
        tie_counts[round_rate(r["tie_rate"])] += 1

    x = list(range(len(bins)))
    width = 0.25

    fig = plt.figure(figsize=(11, 6))
    ax = fig.add_subplot(111)

    ax.bar(
        [i - width for i in x],
        [current_counts[v] for v in bins],
        width=width,
        label="current_peak_rate",
    )

    ax.bar(
        x,
        [strict_counts[v] for v in bins],
        width=width,
        label="strict_peak_rate",
    )

    ax.bar(
        [i + width for i in x],
        [tie_counts[v] for v in bins],
        width=width,
        label="tie_peak_rate",
    )

    ax.set_title(f"Distribution of 3-way peak rates: L={L}, mod={mod_value}")
    ax.set_xlabel("peak_rate")
    ax.set_ylabel("number of seeds")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}/8\n{v:.3f}" for i, v in enumerate(bins)])

    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"保存しました: {save_path}")

# ============================================================
# 10. main
# ============================================================
if __name__ == "__main__":
    run_peak_rate_3way_sweep(
        L=8,
        mod_value=7,
        seed_start=0,
        seed_count=50,
        max_restarts=500,
        min_candidates=10,
    )