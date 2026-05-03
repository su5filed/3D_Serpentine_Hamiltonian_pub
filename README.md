# 3D Hamiltonian Prime Lattice Experiments

## 概要

このリポジトリは、3次元格子 `L × L × L` に対して Snake型ハミルトン路を構成し、その経路に沿って整数

$$
1, 2, \ldots, L^3
$$

を配置したときに現れる合同式的な構造を調べるための実験ノートです。

特に、斜め平面

$$
x + y + z = s
$$

上に配置された奇数番号 `n` の剰余分布について、

$$
L \equiv 1 \pmod m
$$

のとき、

$$
n \equiv s + 1 \pmod m
$$

の剰余クラスにピークが現れる現象を観測しました。

## 現在の状態

これはまだ証明済みの定理ではなく、計算実験に基づく観測および予想です。

## Figures

### Figure 1. Prime positions on a 3D Snake-type Hamiltonian lattice

![Prime positions on a 3D Snake-type Hamiltonian lattice](images/figure1_prime_lattice_L5.png)

### Figure 2. Prime positions by z-layers

![Prime positions by z-layers](images/figure2_prime_layers_L5.png)

## 観測した現象

Snake型ハミルトン配置において、法 `m` に対して `L % m = 1` となる場合、斜め平面 `x+y+z=s` 上の奇数番号 `n` の剰余分布で、最多剰余 `peak_r` が

$$
peak_r \equiv s + 1 \pmod m
$$

となるケースが多数観測されました。

### 主な観測例

| L | mod | L % mod | match / total | rate |
|---:|---:|---:|---:|---:|
| 6 | 5 | 1 | 5/5 | 1.000 |
| 8 | 7 | 1 | 8/8 | 1.000 |
| 11 | 5 | 1 | 12/12 | 1.000 |
| 12 | 11 | 1 | 14/14 | 1.000 |
| 15 | 7 | 1 | 18/18 | 1.000 |
| 16 | 3 | 1 | 20/20 | 1.000 |
| 16 | 5 | 1 | 20/20 | 1.000 |
| 21 | 5 | 1 | 27/27 | 1.000 |
| 22 | 3 | 1 | 29/29 | 1.000 |
| 22 | 7 | 1 | 29/29 | 1.000 |
| 23 | 11 | 1 | 30/30 | 1.000 |
| 26 | 5 | 1 | 35/35 | 1.000 |
| 29 | 7 | 1 | 39/39 | 1.000 |
| 34 | 3 | 1 | 47/47 | 1.000 |
| 34 | 11 | 1 | 47/47 | 1.000 |

一方で、`L % mod != 1` の場合は一致率が低い例が多く観測されました。

例：

| L | mod | L % mod | match / total | rate |
|---:|---:|---:|---:|---:|
| 9 | 7 | 2 | 2/9 | 0.222 |
| 11 | 7 | 4 | 2/12 | 0.167 |
| 29 | 5 | 4 | 1/39 | 0.026 |

## 素数模様との関係

`m` が素数 `p` のとき、

$$
s + 1 \equiv 0 \pmod p
$$

となる斜め平面では、`p` の倍数が多く配置されるため、素数密度が低下する可能性があります。

これは、2次元ウラム螺旋において、線上の数列が多項式となり、その合同性によって素数の出やすさが変わる現象と似ています。

## リポジトリ構成案

```text
3d-hamiltonian-prime-lattice/
├─ README.md
├─ notes/
│  └─ 2026-05-04_modular_residue_peak_note.md
├─ src/
│  ├─ 02_hamiruton_2.py
│  └─ 12_hamiruton.py
├─ logs/
│  └─ 12.txt
└─ images/
   ├─ figure1_prime_lattice_L5.png
   └─ figure2_prime_layers_L5.png
```
ファイルの役割
- src/02_hamiruton_2.py
  3D Snake型ハミルトン路に沿って整数を配置し、素数点を3D表示・画像保存するための可視化用コード。
- src/12_hamiruton.py
  L % mod = 1 のときに剰余ピーク peak_r = (s+1) mod m が現れるかを調べる解析用コード。
- logs/12.txt
  run_mod_sweep() による実験ログ。
- notes/2026-05-04_modular_residue_peak_note.md
  計算実験に基づく研究ノート v0.1。

## 注意

現時点では、以下は未完了です。

- 一般の場合の証明
- 反例探索
- 既存研究との詳細比較
- Snake型以外のハミルトン路との比較
- 方向均衡ハミルトン路で同様の現象が出るかの検証

## 今後の予定

1. Snake型配置の番号式を導出する
2. `L ≡ 1 mod m` のときの剰余分布を証明する
3. 反例探索を行う
4. 方向均衡ハミルトン路との比較実験を行う
5. 3D可視化画像・動画を作成する

## ライセンス

License: To be determined.
