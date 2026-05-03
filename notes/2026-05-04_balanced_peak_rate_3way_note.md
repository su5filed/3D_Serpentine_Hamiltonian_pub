# 2026-05-04 Direction-balanced Hamiltonian Path and 3-way Peak Rate Note

## 目的

本ノートは、Snake型ハミルトン配置で観測された合同ピーク現象が、方向均衡ハミルトン路でも現れるかを比較した記録である。

特に、`L=8, mod=7` の方向均衡ハミルトン路を seed `0..49` で50本生成し、斜め平面 `x+y+z=s` 上の剰余ピークを調べた。

---

## 背景: Snake型での観測

Snake型ハミルトン配置では、法 `m` に対して

$$
L \equiv 1 \pmod m
$$

となる場合、斜め平面 `x+y+z=s` 上の奇数番号 `n` の剰余分布で、最多剰余 `peak_r` が

$$
peak_r \equiv s+1 \pmod m
$$

となるケースが多数観測された。

たとえば、`L=8, mod=7` では

```text
match / total = 8/8
rate = 1.000
```

となった。

---

## 比較対象: 方向均衡ハミルトン路

Snake型は非常に規則的な走査である。そこで、Snake型特有の現象かどうかを調べるため、方向均衡寄りのハミルトン路を探索的に生成した。

方向均衡型では、x方向・y方向・z方向の移動回数がなるべく均等になるようにした。

`L=8` の総移動数は

$$
8^3 - 1 = 511
$$

であり、代表的には

```text
move_counts = {'x': 170, 'y': 170, 'z': 171}
```

のように、ほぼ均等な移動回数になった。

---

## 問題点: peak の同率処理

これまでの `peak_rate` は、剰余カウント配列に対して

```python
counts.index(max_count)
```

を使っていた。

この場合、最大値が複数あると、最初に見つかった剰余だけがピークとして扱われる。

そのため、同率ピークとしては `expected_r` が含まれているのに、既存の `peak_rate` では不一致扱いになるケースがある。

この問題を避けるため、peak_rate を3種類に分けた。

---

## 3種類の peak_rate

斜め平面

$$
s = x+y+z
$$

に対して、期待される剰余を

$$
expected_r \equiv s+1 \pmod m
$$

とする。

| 指標 | 定義 | 意味 |
|---|---|---|
| `current_peak_rate` | `counts.index(max_count) == expected_r` | 既存方式。最大値が複数ある場合、最初の剰余だけを見る |
| `strict_peak_rate` | `expected_r` が単独ピーク | 強い合同ピーク |
| `tie_peak_rate` | `expected_r` が同率ピーク集合に含まれる | 弱い合同ピーク、または出かけている構造 |

---

## 実験条件

```text
L = 8
mod = 7
L % mod = 1
seed_start = 0
seed_count = 50
```

使用コード:

```text
src/22_hamiruton_balanced.py
```

主な実行関数:

```python
run_peak_rate_3way_sweep(
    L=8,
    mod_value=7,
    seed_start=0,
    seed_count=50,
    max_restarts=500,
    min_candidates=10,
)
```

---

## 結果

50 seed すべてでハミルトン路の生成に成功した。

```text
success_count = 50
failed_count  = 0
```

3種類の peak_rate の平均は以下の通り。

| 指標 | 平均値 |
|---|---:|
| `avg_current_rate` | 0.190 |
| `avg_strict_rate` | 0.150 |
| `avg_tie_rate` | 0.302 |

---

## 代表的な seed

| seed | current | strict | tie | 解釈 |
|---:|---:|---:|---:|---|
| 34 | 0.875 | 0.875 | 0.875 | 単独ピークとして非常に強い |
| 47 | 0.125 | 0.125 | 0.625 | currentでは低いが、同率ピークとしては強い |
| 22 | 0.375 | 0.125 | 0.625 | 同率ピークが多い |
| 7 | 0.500 | 0.375 | 0.500 | 中程度に強い |
| 18 | 0.500 | 0.375 | 0.500 | 中程度に強い |
| 31 | 0.500 | 0.375 | 0.500 | 中程度に強い |
| 1 | 0.000 | 0.000 | 0.000 | 合同ピークが出ない |
| 14 | 0.000 | 0.000 | 0.000 | 合同ピークが出ない |

---

## seed=34 について

`seed=34` は、

```text
current = 0.875
strict  = 0.875
tie     = 0.875
```

であり、主要8平面のうち7平面で `expected_r` が単独ピークになっている。

これは、方向均衡型であっても、経路によっては Snake型に近い合同ピークが強く現れることを示している。

---

## seed=47 について

`seed=47` は、

```text
current = 0.125
strict  = 0.125
tie     = 0.625
```

である。

これは、既存の current 判定では合同ピークが弱く見えるが、同率ピークまで含めると、実は `expected_r` がかなり頻繁に局所ピーク集合へ入っていることを意味する。

このような seed は、合同ピークが「出かけている」構造として扱える可能性がある。

---

## modular alignment

合同ピーク現象を直接見るため、次の量を定義する。

$$
e \equiv n - (x+y+z+1) \pmod m
$$

斜め平面 `s=x+y+z` 上では、

$$
e \equiv n - (s+1) \pmod m
$$

となる。

`e=0` が多いほど、

$$
n \equiv s+1 \pmod m
$$

に近い配置である。

ただし、重要なのは全体として `e=0` が多いことだけではない。各斜め平面ごとに `e=0` が局所的に単独ピーク、または同率ピークになっているかが重要である。

---

## 現時点の仮説

### 仮説1: Snake型合同ピーク

Snake型ハミルトン配置では、`L ≡ 1 mod m` のとき、斜め平面上の奇数番号の剰余分布で

$$
peak_r \equiv s+1 \pmod m
$$

が高頻度で成立する。

### 仮説2: 一般ハミルトン路での局所優勢

一般のハミルトン路、特に方向均衡ハミルトン路では、合同ピークは必ずしも出ない。

しかし、

$$
e \equiv n-(x+y+z+1) \pmod m
$$

において、各斜め平面ごとに `e=0` が局所的に優勢になる場合、合同ピークが現れやすい。

### 仮説3: tie_peak_rate は弱い合同構造を捉える

`strict_peak_rate` は強い合同ピークを表し、`tie_peak_rate` は同率ピークとして現れる弱い合同構造を表す。

そのため、今後は `current_peak_rate` よりも、`strict_peak_rate` と `tie_peak_rate` を主指標として扱うのがよい。

---

## 現時点の結論

1. Snake型の合同ピークは、方向均衡ハミルトン路では通常は弱くなる。
2. 方向均衡型でも、seed=34 のように強い合同ピークを示す経路が存在する。
3. current判定だけでは、同率ピークを過小評価する。
4. `strict_peak_rate` と `tie_peak_rate` を分けることで、合同構造の強弱をより正確に見られる。
5. 合同ピーク現象の本体は、経路の方向バランスそのものではなく、斜め平面ごとの modular alignment の局所優勢にある可能性が高い。

---

## 次にやること

1. Snake型にも `current / strict / tie` の3指標を適用する
2. `L=8, mod=7` 以外の組み合わせで方向均衡型 seed sweep を行う
3. `seed=34` と `seed=47` の平面別ヒートマップを研究ノートに追加する
4. 方向均衡型以外のハミルトン路生成法でも同様に調べる
5. Snake型の番号式を導出し、`L ≡ 1 mod m` の合同ピークを証明する
6. 反例探索を行う

---

## 関連ファイル

```text
src/22_hamiruton_balanced.py
logs/22.txt
logs_balanced/peak_rate_3way_L8_mod7_seeds0_49.csv
logs_balanced/peak_rate_3way_L8_mod7_seeds0_49.txt
```
