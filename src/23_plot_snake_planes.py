import math
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# =========================================================
# 基本関数
# =========================================================

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    r = int(math.isqrt(n))
    for d in range(3, r + 1, 2):
        if n % d == 0:
            return False
    return True


def snake_hamiltonian_path_3d(L: int):
    """
    L x L x L 格子上の Snake 型ハミルトン路を返す。
    path[k] = (x, y, z)
    """
    path = []

    for z in range(L):
        y_range = range(L) if z % 2 == 0 else range(L - 1, -1, -1)

        for yi, y in enumerate(y_range):
            # 行ごとに x 方向を往復
            if (z % 2 == 0 and yi % 2 == 0) or (z % 2 == 1 and yi % 2 == 1):
                x_range = range(L)
            else:
                x_range = range(L - 1, -1, -1)

            for x in x_range:
                path.append((x, y, z))

    return path


def build_number_maps(path):
    """
    path の順に 1,2,3,... を振る
    coord_to_number[(x,y,z)] = n
    number_to_coord[n] = (x,y,z)
    """
    coord_to_number = {}
    number_to_coord = {}

    for i, coord in enumerate(path, start=1):
        coord_to_number[coord] = i
        number_to_coord[i] = coord

    return coord_to_number, number_to_coord


def collect_prime_positions(coord_to_number):
    """
    素数の格子点座標を返す
    """
    prime_coords = []
    prime_numbers = []

    for coord, n in coord_to_number.items():
        if is_prime(n):
            prime_coords.append(coord)
            prime_numbers.append(n)

    return prime_coords, prime_numbers


# =========================================================
# 平面 x+y+z=s を立方体 [0, L-1]^3 と交わらせた多角形を作る
# =========================================================

def plane_cube_intersection_polygon(L: int, s: int, eps=1e-9):
    """
    立方体 0<=x,y,z<=L-1 と平面 x+y+z=s の交線ポリゴン頂点を返す。
    頂点は3D座標の list[(x,y,z), ...]。
    """
    a = 0.0
    b = float(L - 1)

    # 立方体の12辺
    edges = []

    # x方向辺
    for y in [a, b]:
        for z in [a, b]:
            edges.append(((a, y, z), (b, y, z)))

    # y方向辺
    for x in [a, b]:
        for z in [a, b]:
            edges.append(((x, a, z), (x, b, z)))

    # z方向辺
    for x in [a, b]:
        for y in [a, b]:
            edges.append(((x, y, a), (x, y, b)))

    pts = []

    for p1, p2 in edges:
        x1, y1, z1 = p1
        x2, y2, z2 = p2

        v1 = x1 + y1 + z1 - s
        v2 = x2 + y2 + z2 - s

        # 辺全体が平面上にある場合
        if abs(v1) < eps and abs(v2) < eps:
            pts.append(p1)
            pts.append(p2)
            continue

        # 片方の端点が平面上
        if abs(v1) < eps:
            pts.append(p1)
        if abs(v2) < eps:
            pts.append(p2)

        # 符号が異なれば交点あり
        if v1 * v2 < -eps:
            t = v1 / (v1 - v2)
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            z = z1 + t * (z2 - z1)
            pts.append((x, y, z))

    # 重複除去
    uniq = []
    for p in pts:
        if not any(
            abs(p[0] - q[0]) < 1e-7 and
            abs(p[1] - q[1]) < 1e-7 and
            abs(p[2] - q[2]) < 1e-7
            for q in uniq
        ):
            uniq.append(p)

    if len(uniq) < 3:
        return []

    # 平面上の点を並び替える
    pts_np = np.array(uniq, dtype=float)
    center = pts_np.mean(axis=0)

    # 平面法線
    normal = np.array([1.0, 1.0, 1.0])
    normal = normal / np.linalg.norm(normal)

    # 平面内基底ベクトル u, v
    # normal に直交する適当なベクトル
    tmp = np.array([1.0, -1.0, 0.0])
    if abs(np.dot(tmp, normal)) > 0.99:
        tmp = np.array([1.0, 0.0, -1.0])

    u = tmp - np.dot(tmp, normal) * normal
    u = u / np.linalg.norm(u)
    v = np.cross(normal, u)
    v = v / np.linalg.norm(v)

    # 角度順にソート
    angles = []
    for p in pts_np:
        d = p - center
        angle = math.atan2(np.dot(d, v), np.dot(d, u))
        angles.append(angle)

    order = np.argsort(angles)
    polygon = [tuple(pts_np[i]) for i in order]

    return polygon


# =========================================================
# 描画
# =========================================================

def plot_snake_prime_lattice_with_planes(
    L=15,
    plane_values=(6, 20, 34),
    save_path="images/figure_snake_prime_lattice_planes_L15.png",
    show_path=True,
    annotate_primes=False
):
    """
    Snake型ハミルトン配置 + 素数位置 + 斜め平面 x+y+z=s を描く
    """
    path = snake_hamiltonian_path_3d(L)
    coord_to_number, number_to_coord = build_number_maps(path)
    prime_coords, prime_numbers = collect_prime_positions(coord_to_number)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    fig = plt.figure(figsize=(12, 9), dpi=150)
    ax = fig.add_subplot(111, projection='3d')

    # -------------------------------------------------
    # 全格子点
    # -------------------------------------------------
    xs_all = [p[0] + 1 for p in path]
    ys_all = [p[1] + 1 for p in path]
    zs_all = [p[2] + 1 for p in path]

    ax.scatter(
        xs_all, ys_all, zs_all,
        s=4, alpha=0.20, c='gray',
        label=f"All lattice points\n(1 to {L**3})"
    )

    # -------------------------------------------------
    # ハミルトン路（かなり薄く）
    # -------------------------------------------------
    if show_path:
        ax.plot(
            xs_all, ys_all, zs_all,
            color='gray', linewidth=0.7, alpha=0.35,
            label="Hamiltonian snake path\n(very faint)"
        )

    # -------------------------------------------------
    # 素数位置
    # -------------------------------------------------
    xs_p = [p[0] + 1 for p in prime_coords]
    ys_p = [p[1] + 1 for p in prime_coords]
    zs_p = [p[2] + 1 for p in prime_coords]

    ax.scatter(
        xs_p, ys_p, zs_p,
        s=26,
        c='#1f77ff',
        edgecolors='white',
        linewidths=0.7,
        alpha=0.95,
        label="Prime positions\nin Hamiltonian order"
    )

    if annotate_primes:
        for coord, n in zip(prime_coords, prime_numbers):
            x, y, z = coord
            ax.text(x + 1, y + 1, z + 1, str(n), fontsize=5)

    # -------------------------------------------------
    # 平面 x+y+z=s
    # 注意: ここで格子座標は 0..L-1 で扱っているので、
    # 描画時は +1 して 1..L に見せる
    # -------------------------------------------------
    plane_colors = ['#f6b26b', '#e566c1', '#f4dd62']  # オレンジ, ピンク, 黄
    plane_handles = []

    for idx, s in enumerate(plane_values):
        poly = plane_cube_intersection_polygon(L, s)
        if not poly:
            continue

        poly_shifted = [(x + 1, y + 1, z + 1) for (x, y, z) in poly]
        color = plane_colors[idx % len(plane_colors)]

        pc = Poly3DCollection(
            [poly_shifted],
            facecolors=color,
            edgecolors=color,
            linewidths=1.0,
            alpha=0.35
        )
        ax.add_collection3d(pc)
        plane_handles.append((color, s))

    # -------------------------------------------------
    # 軸など
    # -------------------------------------------------
    ax.set_xlim(1, L)
    ax.set_ylim(1, L)
    ax.set_zlim(1, L)

    ax.set_xlabel("x", fontsize=14)
    ax.set_ylabel("y", fontsize=14)
    ax.set_zlabel("z", fontsize=14)

    ax.set_xticks(range(1, L + 1, 2))
    ax.set_yticks(range(1, L + 1, 2))
    ax.set_zticks(range(1, L + 1, 2))

    title = (
        f"{L} × {L} × {L} Lattice ({L**3} Points)\n"
        f"Snake Hamiltonian Ordering of Integers 1–{L**3}\n"
        f"Prime-Number Positions Highlighted"
    )
    ax.set_title(title, fontsize=15, pad=20)

    # 見やすい角度
    ax.view_init(elev=17, azim=-66)

    # -------------------------------------------------
    # 凡例
    # -------------------------------------------------
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    legend_items = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#1f77ff', markeredgecolor='white',
               markersize=7, label='Prime positions\nin Hamiltonian order'),
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor='gray', alpha=0.5,
               markersize=4, label=f'All lattice points\n(1 to {L**3})'),
        Line2D([0], [0], color='gray', alpha=0.6,
               label='Hamiltonian snake path\n(very faint)')
    ]

    # 平面凡例
    if plane_handles:
        legend_items.append(Patch(facecolor='none', edgecolor='none',
                                  label='Diagonal Planes  x + y + z = k'))
        for color, s in plane_handles:
            legend_items.append(Patch(facecolor=color, edgecolor=color, alpha=0.7,
                                      label=f'x + y + z = {s}'))

    ax.legend(
        handles=legend_items,
        loc='upper left',
        bbox_to_anchor=(1.02, 0.85),
        frameon=True,
        borderpad=1.0,
        labelspacing=1.0
    )

    # -------------------------------------------------
    # 右下情報ボックス
    # -------------------------------------------------
    prime_count = len(prime_numbers)
    info_text = (
        f"Grid:  1 ≤ x, y, z ≤ {L}\n"
        f"Total points:  {L}³ = {L**3}\n"
        f"Primes ≤ {L**3}:  {prime_count}"
    )

    fig.text(
        0.76, 0.12, info_text,
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.5", facecolor='white', edgecolor='gray', alpha=0.9)
    )

    # -------------------------------------------------
    # 左下の簡易座標アイコン
    # -------------------------------------------------
    fig.text(0.06, 0.085, "z", fontsize=14)
    fig.text(0.11, 0.055, "y", fontsize=14)
    fig.text(0.08, 0.02, "x", fontsize=14)
    plt.annotate("", xy=(0.07, 0.08), xytext=(0.07, 0.02),
                 xycoords='figure fraction',
                 arrowprops=dict(arrowstyle='-|>', lw=1.5, color='black'))
    plt.annotate("", xy=(0.11, 0.055), xytext=(0.07, 0.02),
                 xycoords='figure fraction',
                 arrowprops=dict(arrowstyle='-|>', lw=1.5, color='black'))
    plt.annotate("", xy=(0.12, 0.02), xytext=(0.07, 0.02),
                 xycoords='figure fraction',
                 arrowprops=dict(arrowstyle='-|>', lw=1.5, color='black'))

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    plt.show()

    print("保存しました:", save_path)


# =========================================================
# 実行
# =========================================================

if __name__ == "__main__":
    plot_snake_prime_lattice_with_planes(
        L=15,
        plane_values=(6, 20, 34),
        save_path="images/figure_snake_prime_lattice_planes_L15.png",
        show_path=True,
        annotate_primes=False
    )