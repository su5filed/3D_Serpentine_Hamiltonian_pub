import math
from itertools import product
import matplotlib.pyplot as plt


# =========================
# 1. 素数判定（エラトステネス）
# =========================
def sieve_primes(n):
    """
    1..n の素数判定表を返す
    is_prime[k] = True なら k は素数
    """
    if n < 2:
        return [False] * (n + 1)

    is_prime = [True] * (n + 1)
    is_prime[0] = False
    is_prime[1] = False

    limit = int(math.isqrt(n))
    for p in range(2, limit + 1):
        if is_prime[p]:
            start = p * p
            step = p
            for x in range(start, n + 1, step):
                is_prime[x] = False

    return is_prime


# =========================
# 2. 3D ハミルトン路（Snake型）
# =========================
def hamiltonian_snake_3d(L):
    """
    L x L x L 格子点を全部1回ずつ通る簡単なハミルトン路を返す
    返り値: [(x,y,z), ...]
    """
    path = []

    for z in range(L):
        y_range = range(L) if z % 2 == 0 else range(L - 1, -1, -1)

        for y in y_range:
            # z と y の偶奇に応じて x の向きを切り替える
            if (z % 2 == 0 and y % 2 == 0) or (z % 2 == 1 and y % 2 == 1):
                x_range = range(L)
            else:
                x_range = range(L - 1, -1, -1)

            for x in x_range:
                path.append((x, y, z))

    return path


# =========================
# 3. ハミルトン路の妥当性チェック
# =========================
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


# =========================
# 4. 数字の配置
# =========================
def assign_numbers_to_path(path):
    """
    path[0] に 1, path[1] に 2, ... を対応づける
    戻り値:
      number_to_coord: {number: (x,y,z)}
      coord_to_number: {(x,y,z): number}
    """
    number_to_coord = {}
    coord_to_number = {}

    for i, coord in enumerate(path, start=1):
        number_to_coord[i] = coord
        coord_to_number[coord] = i

    return number_to_coord, coord_to_number


# =========================
# 5. 素数点の抽出
# =========================
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


# =========================
# 6. 3D表示
# =========================
def plot_prime_3d(L, path, prime_points, prime_numbers, show_path=False, annotate_prime=False):
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 全格子点を薄く表示
    all_points = list(product(range(L), range(L), range(L)))
    ax.scatter(
        [p[0] for p in all_points],
        [p[1] for p in all_points],
        [p[2] for p in all_points],
        s=15,
        alpha=0.12,
        label="all lattice points"
    )

    # 一筆書き経路を薄く表示
    if show_path:
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        zs = [p[2] for p in path]
        ax.plot(xs, ys, zs, linewidth=1.0, alpha=0.35, label="Hamiltonian path")

    # 素数点を強調
    ax.scatter(
        [p[0] for p in prime_points],
        [p[1] for p in prime_points],
        [p[2] for p in prime_points],
        s=60,
        alpha=0.95,
        marker='o',
        label="primes"
    )

    # 必要なら素数の値も表示
    if annotate_prime:
        for coord, n in zip(prime_points, prime_numbers):
            ax.text(coord[0], coord[1], coord[2], str(n), fontsize=8)

    ax.set_title(f"3D Prime Pattern on {L}x{L}x{L} Hamiltonian Lattice")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_xlim(0, L - 1)
    ax.set_ylim(0, L - 1)
    ax.set_zlim(0, L - 1)
    ax.set_box_aspect((L, L, L))
    ax.legend()
    plt.tight_layout()
    plt.show()


# =========================
# 7. 各 z 層の2D表示
# =========================
def plot_prime_layers(L, coord_to_number):
    """
    各 z 層を2Dのマス目として表示
    素数のマスを黒、非素数を白で表示
    """
    N = L ** 3
    is_prime = sieve_primes(N)

    fig, axes = plt.subplots(1, L, figsize=(4 * L, 4))
    if L == 1:
        axes = [axes]

    for z in range(L):
        grid = [[0 for _ in range(L)] for _ in range(L)]

        for y in range(L):
            for x in range(L):
                n = coord_to_number[(x, y, z)]
                grid[L - 1 - y][x] = 1 if is_prime[n] else 0

        ax = axes[z]
        ax.imshow(grid, interpolation="nearest")
        ax.set_title(f"z = {z}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_xticks(range(L))
        ax.set_yticks(range(L))

        # 数字をマスに書く
        for y in range(L):
            for x in range(L):
                n = coord_to_number[(x, L - 1 - y, z)]
                color = "white" if is_prime[n] else "black"
                ax.text(x, y, str(n), ha="center", va="center", fontsize=8, color=color)

    plt.tight_layout()
    plt.show()


# =========================
# 8. 簡単な統計
# =========================
def print_basic_stats(L, prime_points, prime_numbers):
    print("=" * 60)
    print(f"L = {L}")
    print(f"総点数 N = {L**3}")
    print(f"素数個数 = {len(prime_numbers)}")
    print(f"素数一覧 = {prime_numbers}")

    # z層ごとの素数個数
    z_count = [0] * L
    for x, y, z in prime_points:
        z_count[z] += 1
    print("z層ごとの素数個数:", z_count)

    # x+y+z ごとの個数
    diag_count = {}
    for x, y, z in prime_points:
        s = x + y + z
        diag_count[s] = diag_count.get(s, 0) + 1
    print("x+y+z ごとの素数個数:", dict(sorted(diag_count.items())))


# =========================
# 9. 実行関数
# =========================
def run_experiment(L=5, show_path=True, annotate_prime=False):
    path = hamiltonian_snake_3d(L)

    ok, msg = verify_hamiltonian_path(path, L)
    print("ハミルトン路チェック:", msg)
    if not ok:
        return

    prime_points, prime_numbers, number_to_coord, coord_to_number = collect_prime_points(L, path)

    print_basic_stats(L, prime_points, prime_numbers)
    
    analyze_diagonal_planes(L, coord_to_number)

    plot_prime_3d(L, path, prime_points, prime_numbers, show_path=show_path, annotate_prime=annotate_prime)
    plot_prime_layers(L, coord_to_number)

def analyze_diagonal_planes(L, coord_to_number):
    """
    x+y+z = s ごとの
    ・格子点数
    ・素数個数
    ・素数密度
    を表示する
    """
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

    print("=" * 60)
    print("x+y+z 斜め平面ごとの素数密度")
    print("s | total | prime | density")
    print("-" * 40)

    for s in sorted(plane_total.keys()):
        total = plane_total[s]
        prime = plane_prime.get(s, 0)
        density = prime / total if total > 0 else 0.0

        print(f"{s:2d} | {total:5d} | {prime:5d} | {density:7.3f}")
def summarize_diagonal_planes(L, coord_to_number):
    """
    x+y+z=s ごとの total, prime, density を辞書で返す
    """
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

    rows = []
    for s in sorted(plane_total.keys()):
        total = plane_total[s]
        prime = plane_prime.get(s, 0)
        density = prime / total if total > 0 else 0.0
        rows.append({
            "s": s,
            "total": total,
            "prime": prime,
            "density": density
        })

    return rows


def run_l_sweep(L_values=(5, 7, 9, 11, 15)):
    """
    Lを変えながら、斜め平面 x+y+z=s の素数密度を比較する
    """
    for L in L_values:
        print("\n" + "=" * 80)
        print(f"L = {L}")
        print("=" * 80)

        path = hamiltonian_snake_3d(L)

        ok, msg = verify_hamiltonian_path(path, L)
        print("ハミルトン路チェック:", msg)
        if not ok:
            continue

        prime_points, prime_numbers, number_to_coord, coord_to_number = collect_prime_points(L, path)

        print(f"総点数 N = {L**3}")
        print(f"素数個数 = {len(prime_numbers)}")
        print(f"素数密度 = {len(prime_numbers) / (L**3):.4f}")

        rows = summarize_diagonal_planes(L, coord_to_number)

        print("s | total | prime | density | parity")
        print("-" * 55)

        for r in rows:
            s = r["s"]
            parity = "even" if s % 2 == 0 else "odd"
            print(
                f"{s:2d} | "
                f"{r['total']:5d} | "
                f"{r['prime']:5d} | "
                f"{r['density']:7.3f} | "
                f"{parity}"
            )
        
        analyze_even_plane_bias(L, coord_to_number) # 偶数平面の偏り解析も行う

        analyze_even_plane_bias_log_model(L, coord_to_number) # 1/log(n) 補正モデルでの解析も行う

        analyze_small_prime_divisibility(L, coord_to_number) # 小さい素数による割り切れ率解析も行う

        safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=18) # s=18 での 7 の剰余クラス分布も見てみる
        safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=20) # s=20 での 7 の剰余クラス分布も見てみる
        safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=22) # s=22 での 7 の剰余クラス分布も見てみる
        safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=24) # s=24 での 7 の剰余クラス分布も見てみる
        safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=34) # s=34 での 7 の剰余クラス分布も見てみる

        analyze_mod_residue_peaks_by_plane(L, coord_to_number, mod_value=7) # sごとの7の剰余クラス分布のピークを分析する

        summarize_peak_match_rate(L, coord_to_number, mod_value=7) # ピークと全体の一致率をまとめて表示する

def analyze_even_plane_bias(L, coord_to_number):
    """
    偶数 s = x+y+z 平面について、
    素数個数が期待値より多いか少ないかを見る。

    ここでは 2 を除外し、
    3以上の奇数素数だけを対象にする。
    """
    N = L ** 3
    is_prime = sieve_primes(N)

    # 3以上の奇数候補数
    # 1 は素数でないので除外
    total_odd_candidates = 0
    total_odd_primes = 0

    for n in range(3, N + 1, 2):
        total_odd_candidates += 1
        if is_prime[n]:
            total_odd_primes += 1

    p_global = total_odd_primes / total_odd_candidates

    print("=" * 80)
    print("偶数 s 平面の偏り解析")
    print(f"L = {L}")
    print(f"N = {N}")
    print(f"3以上の奇数候補数 = {total_odd_candidates}")
    print(f"3以上の奇数素数数 = {total_odd_primes}")
    print(f"奇数候補内の素数密度 = {p_global:.4f}")
    print()
    print("s | total | candidates | prime | expected | diff | z")
    print("-" * 75)

    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        total = 0
        candidates = 0
        prime_count = 0

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    total += 1
                    n = coord_to_number[(x, y, z)]

                    # 今回は 3以上の奇数だけ対象
                    if n >= 3 and n % 2 == 1:
                        candidates += 1
                        if is_prime[n]:
                            prime_count += 1

        if candidates == 0:
            continue

        expected = candidates * p_global
        var = candidates * p_global * (1.0 - p_global)
        z_score = (prime_count - expected) / math.sqrt(var) if var > 0 else 0.0
        diff = prime_count - expected

        rows.append((s, total, candidates, prime_count, expected, diff, z_score))

    # zスコアの絶対値が大きい順にも使えるようにする
    for s, total, candidates, prime_count, expected, diff, z_score in rows:
        print(
            f"{s:2d} | "
            f"{total:5d} | "
            f"{candidates:10d} | "
            f"{prime_count:5d} | "
            f"{expected:8.2f} | "
            f"{diff:6.2f} | "
            f"{z_score:6.2f}"
        )

    print()
    print("zスコア絶対値 上位")
    print("-" * 75)

    rows_sorted = sorted(rows, key=lambda r: abs(r[6]), reverse=True)

    for s, total, candidates, prime_count, expected, diff, z_score in rows_sorted[:10]:
        print(
            f"s={s:2d}, "
            f"prime={prime_count:4d}, "
            f"expected={expected:7.2f}, "
            f"diff={diff:7.2f}, "
            f"z={z_score:6.2f}, "
            f"candidates={candidates}"
        )

def analyze_even_plane_bias_log_model(L, coord_to_number):
    """
    1/log(n) による素数密度補正モデル。
    各平面に実際に置かれた n を見て、
    expected = Σ 1/log(n)
    var      = Σ p(n)(1-p(n))
    z        = (observed - expected) / sqrt(var)

    3以上の奇数のみ対象。
    """
    import math

    N = L ** 3
    is_prime = sieve_primes(N)

    print("=" * 80)
    print("偶数 s 平面の偏り解析：log補正モデル")
    print(f"L = {L}")
    print(f"N = {N}")
    print()
    print("s | candidates | prime | expected_log | diff | z | avg_n")
    print("-" * 80)

    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        candidates = 0
        prime_count = 0
        expected = 0.0
        variance = 0.0
        sum_n = 0

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    # 3以上の奇数のみ対象
                    if n < 3 or n % 2 == 0:
                        continue

                    candidates += 1
                    sum_n += n

                    if is_prime[n]:
                        prime_count += 1

                    # 奇数に限定しているので、素数密度を少し補正
                    # 奇数の中での素数確率として 2/log(n) を使う
                    # ただし 1 を超えないようにする
                    p = 2.0 / math.log(n)
                    if p > 1.0:
                        p = 1.0

                    expected += p
                    variance += p * (1.0 - p)

        if candidates == 0:
            continue

        z_score = (prime_count - expected) / math.sqrt(variance) if variance > 0 else 0.0
        diff = prime_count - expected
        avg_n = sum_n / candidates

        rows.append((s, candidates, prime_count, expected, diff, z_score, avg_n))

    for s, candidates, prime_count, expected, diff, z_score, avg_n in rows:
        print(
            f"{s:2d} | "
            f"{candidates:10d} | "
            f"{prime_count:5d} | "
            f"{expected:12.2f} | "
            f"{diff:7.2f} | "
            f"{z_score:6.2f} | "
            f"{avg_n:8.1f}"
        )

    print()
    print("log補正 zスコア絶対値 上位")
    print("-" * 80)

    rows_sorted = sorted(rows, key=lambda r: abs(r[5]), reverse=True)

    for s, candidates, prime_count, expected, diff, z_score, avg_n in rows_sorted[:10]:
        print(
            f"s={s:2d}, "
            f"prime={prime_count:4d}, "
            f"expected_log={expected:8.2f}, "
            f"diff={diff:8.2f}, "
            f"z={z_score:6.2f}, "
            f"candidates={candidates:4d}, "
            f"avg_n={avg_n:8.1f}"
        )


def analyze_small_prime_divisibility(L, coord_to_number, small_primes=(3, 5, 7, 11, 13, 17)):
    """
    各偶数 s 平面に置かれた 3以上の奇数 n について、
    小さい素数で割り切れる割合を調べる。

    目的:
      s=20 などで素数が少ない理由が、
      小さい素数の倍数の多さによるものかを見る。
    """
    N = L ** 3
    is_prime = sieve_primes(N)

    print("=" * 80)
    print("小さい素数による割り切れ率解析")
    print(f"L = {L}")
    print()
    header = "s | cand | prime "
    for p in small_primes:
        header += f"| div{p:02d} "
    header += "| composite_by_small"
    print(header)
    print("-" * len(header))

    rows = []

    for s in range(0, 3 * (L - 1) + 1):
        candidates = []
        prime_count = 0

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    # 3以上の奇数だけ対象
                    if n < 3 or n % 2 == 0:
                        continue

                    candidates.append(n)
                    if is_prime[n]:
                        prime_count += 1

        if not candidates:
            continue

        div_counts = {}
        small_composite_set = set()

        for p in small_primes:
            cnt = 0
            for n in candidates:
                # n=p 自身は素数なので「割り切れる合成数」としては扱わない
                if n != p and n % p == 0:
                    cnt += 1
                    small_composite_set.add(n)
            div_counts[p] = cnt

        cand = len(candidates)
        composite_by_small = len(small_composite_set)

        rows.append((s, cand, prime_count, div_counts, composite_by_small))

    for s, cand, prime_count, div_counts, composite_by_small in rows:
        line = f"{s:2d} | {cand:4d} | {prime_count:5d} "
        for p in small_primes:
            rate = div_counts[p] / cand
            line += f"| {rate:5.2f} "
        line += f"| {composite_by_small:5d} ({composite_by_small/cand:5.2f})"
        print(line)

    print()
    print("小さい素数で割れる合成数が多い順")
    print("-" * 80)

    rows_sorted = sorted(rows, key=lambda r: r[4] / r[1], reverse=True)

    for s, cand, prime_count, div_counts, composite_by_small in rows_sorted[:10]:
        print(
            f"s={s:2d}, "
            f"cand={cand:4d}, "
            f"prime={prime_count:4d}, "
            f"small_composite={composite_by_small:4d}, "
            f"rate={composite_by_small/cand:5.2f}, "
            + ", ".join([f"div{p}={div_counts[p]}" for p in small_primes])
        )

def safe_analyze_residue_distribution(L, coord_to_number, mod_values=(7,), target_s=None):
    max_s = 3 * (L - 1)

    if target_s is not None and not (0 <= target_s <= max_s):
        print("=" * 80)
        print("剰余分布解析 skipped")
        print(f"L={L}, target_s={target_s} は範囲外です。max_s={max_s}")
        return

    analyze_residue_distribution(
        L,
        coord_to_number,
        mod_values=mod_values,
        target_s=target_s
    )

def analyze_residue_distribution(L, coord_to_number, mod_values=(3, 5, 7, 11, 13, 17), target_s=None):
    """
    x+y+z=s 平面ごと、または target_s 指定で、
    配置された奇数 n の mod 分布を調べる。
    """
    print("=" * 80)
    print("剰余分布解析")
    print(f"L = {L}")
    if target_s is not None:
        print(f"target_s = {target_s}")
    print()

    s_values = [target_s] if target_s is not None else range(0, 3 * (L - 1) + 1)

    for s in s_values:
        if s is None:
            continue

        nums = []

        for x in range(L):
            for y in range(L):
                for z in range(L):
                    if x + y + z != s:
                        continue

                    n = coord_to_number[(x, y, z)]

                    # 3以上の奇数だけ対象
                    if n >= 3 and n % 2 == 1:
                        nums.append(n)

        if not nums:
            continue

        print("-" * 80)
        print(f"s = {s}, candidates = {len(nums)}")
        print(f"min_n={min(nums)}, max_n={max(nums)}, avg_n={sum(nums)/len(nums):.1f}")

        for m in mod_values:
            counts = [0] * m
            for n in nums:
                counts[n % m] += 1

            print(f"mod {m}:")
            for r, cnt in enumerate(counts):
                if cnt > 0:
                    print(f"  r={r:2d}: {cnt:4d} ({cnt/len(nums):.3f})")

def analyze_mod_residue_peaks_by_plane(L, coord_to_number, mod_value=7):
    """
    各偶数 s=x+y+z 平面について、
    奇数 n の mod 分布のピークを調べる。

    見たいもの:
      peak_r が s+1 mod mod_value と一致するか
      r=0 が多い平面で素数が少ないか
    """
    print("=" * 80)
    print(f"mod {mod_value} 剰余ピーク解析")
    print(f"L = {L}")
    print()
    print("s | cand | peak_r | peak_count | peak_rate | r0_count | r0_rate | expected_peak")
    print("-" * 95)

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

def summarize_peak_match_rate(L, coord_to_number, mod_value=7):
    """
    各偶数 s について、
    peak_r == (s+1) % mod_value
    がどれくらい成立するかを集計する。
    端の小さい候補数は除外できる。
    """
    total = 0
    match = 0
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

        # 候補数が少なすぎる端は除外
        if len(nums) < 10:
            continue

        counts = [0] * mod_value
        for n in nums:
            counts[n % mod_value] += 1

        peak_count = max(counts)
        peak_r = counts.index(peak_count)
        expected = (s + 1) % mod_value

        ok = (peak_r == expected)

        total += 1
        if ok:
            match += 1

        rows.append((s, len(nums), peak_r, expected, peak_count, peak_count / len(nums), ok))

    rate = match / total if total > 0 else 0.0

    print("=" * 80)
    print(f"peak一致率 summary: L={L}, mod={mod_value}")
    print(f"match = {match}/{total}, rate = {rate:.3f}")
    print("s | cand | peak_r | expected | peak_rate | result")
    print("-" * 70)

    for s, cand, peak_r, expected, peak_count, peak_rate, ok in rows:
        result = "OK" if ok else "--"
        print(
            f"{s:2d} | {cand:4d} | {peak_r:6d} | "
            f"{expected:8d} | {peak_rate:9.3f} | {result}"
        )

def run_mod_sweep(L_values=(6, 8, 11, 15, 16, 21, 22, 26, 29),
                  mod_values=(3, 5, 7, 11)):
    """
    L と mod を変えて、
    peak_r == (s+1) % mod
    の一致率を比較する。
    """
    print("=" * 90)
    print("L と mod の peak一致率まとめ")
    print("L | mod | L%mod | match/total | rate")
    print("-" * 90)

    for L in L_values:
        path = hamiltonian_snake_3d(L)
        ok, msg = verify_hamiltonian_path(path, L)
        if not ok:
            print(f"L={L}: NG {msg}")
            continue

        _, _, _, coord_to_number = collect_prime_points(L, path)

        for mod_value in mod_values:
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

                if len(nums) < 10:
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

            print(
                f"{L:2d} | "
                f"{mod_value:3d} | "
                f"{L % mod_value:5d} | "
                f"{match:3d}/{total:<3d} | "
                f"{rate:5.3f}"
            )

if __name__ == "__main__":
    # まずは小さく試す
    #run_experiment(L=5, show_path=True, annotate_prime=False)
    #run_l_sweep(L_values=(5, 7, 9, 11, 15))
    #run_l_sweep(L_values=(8, 9, 11, 15, 22, 29))
    
    # L と mod を変えて、ピークの一致率をまとめてみる
    run_mod_sweep(
        L_values=(6, 8, 11, 12, 15, 16, 21, 22, 23, 26, 29, 34),
        mod_values=(3, 5, 7, 11)
    )
