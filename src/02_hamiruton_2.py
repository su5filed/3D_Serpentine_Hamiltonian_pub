import math
from itertools import product
import matplotlib.pyplot as plt
import os

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
def plot_prime_3d(L, path, prime_points, prime_numbers, show_path=False, annotate_prime=False, save_path=None):
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
    #plt.tight_layout()
    #plt.show()
    plt.tight_layout()

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=220, bbox_inches="tight")
        print(f"保存しました: {save_path}")

    plt.close(fig)



# =========================
# 7. 各 z 層の2D表示
# =========================
def plot_prime_layers(L, coord_to_number, save_path=None):
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
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=220, bbox_inches="tight")
        print(f"保存しました: {save_path}")
    plt.close(fig)


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
    #plot_prime_3d(L, path, prime_points, prime_numbers, show_path=show_path, annotate_prime=annotate_prime)
    #plot_prime_layers(L, coord_to_number)
    plot_prime_3d(
        L,
        path,
        prime_points,
        prime_numbers,
        show_path=show_path,
        annotate_prime=annotate_prime,
        save_path=f"images/figure1_prime_lattice_L{L}.png"
    )

    plot_prime_layers(
        L,
        coord_to_number,
        save_path=f"images/figure2_prime_layers_L{L}.png"
    )


if __name__ == "__main__":
    # まずは小さく試す
    run_experiment(L=5, show_path=True, annotate_prime=False)