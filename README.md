# 荧（原神）→ X4: Foundations **女性** NPC（泰伦 / 阿贡）

把《原神》女主角**荧**的模型移植成《X4：基石》里的女性 NPC 外观，替换头部与躯干网格。

**两种目标种族、两种形态，都由命令行参数决定**：

```bash
python tools/make_mod.py --race <terran|argon> --mode <add|replace> [--weight N]
```

| | 形态 | 做法 | 覆盖范围 |
|---|---|---|---|
| `--mode add`（**默认**） | 加入外观池 | 新增一条 macro（`<add sel="/macros">`，`ref` 该种族 cau base macro），并往每个该种族女性外观池追加一条 `<select>` | 泰伦/先驱者 **12 个池**；阿贡 **6 个池**。原版 macro 一个不动，她只是"随机出现的其中一个"（3 候选池 1/4，阿贡平民池 6 候选 1/7）。**剧情/任务 NPC 不走外观池，保持原版** |
| `--mode replace` | 全部替换 | 把该种族女性 macro 的 `<models>` **逐个改写**成荧的头/躯干 | 泰伦 **45 个 macro**（清单由 `tools/find_terran_female_macros.py` 生成，写在 `work/terran_female_macros.json`），含不走池的剧情 NPC |

两个种族**共用同一个 component**（`character_argon_female_01`），网格完全一样，
所以两个版本只是 base macro 不同（决定她的 `race` 标记）和进的池不同；
阿贡版与泰伦版可以同时安装。

这是本工作区的**第三个** X4 角色 mod，也是第一个做了两个目标种族的。管线骨架沿用
[`x4-character-retarget`](https://github.com/tridkx/x4-character-retarget)
（萝丝 → X4 Argon），但**目标种族换了（Argon → Terran）**，
按 skill 的要求把每一处都重新量了一遍。

## 与另外两个项目的关键差异

| | 萝丝 / 艾梅莉埃 | 荧 |
|---|---|---|
| 目标 | Argon 女性 | **Terran（+ Pioneers）女性，另可做 Argon 女性** |
| 默认替换方式 | 改外观池（charactergroups） | 改外观池（add）/ 逐个 macro 覆盖 `<models>`（replace） |
| 覆盖范围 | 池内随机 NPC | add：12 池（泰伦）/ 6 池（阿贡）；replace：45 个 macro（含剧情 NPC） |

**Terran 女性与 Argon 女性共用同一个 component**，所以骨架、动画、host 模板全部复用；
但**每个 Terran 派生 macro 都重写自己的 `<models>`**，改 base 无效 —— 所以泰伦的
"全部替换"必须逐个 macro 改（`--mode replace`），这也顺带覆盖了不经过外观池的
剧情 NPC；而阿贡的派生 macro 继承 base 的 `<models>`，改池就够。

## 复现

```bash
python   tools/find_terran_female_macros.py                        # 生成 45 个 macro 清单（replace 用）
python   tools/prepare_textures_lumine.py                          # 贴图 → DDS + manifest
blender -b --factory-startup --python tools/build_lumine_x4.py      # 阶段1：重定向
blender -b --factory-startup --python tools/build_lumine_mod.py     # 阶段2：导出 .xac
python   tools/make_mod.py --race terran --mode add                 # 组装 mod 树（默认形态）
python   tools/make_mod.py --race argon  --mode add                 # 阿贡版（进阿贡 6 个池）
python   tools/make_mod.py --race terran --mode replace             # 全部替换版
python   tools/verify_mod.py --race terran --mode add               # 发版自检（参数要跟产物一致）
XRCatTool.exe -in work/x4_lumine_terran_add -out work/x4_lumine_terran_add/ext_01.cat
```

输出目录按「种族 + 形态」分开（互不覆盖，发布时并存）：
`work/x4_lumine_terran_add` / `work/x4_lumine_terran_replace` / `work/x4_lumine_argon_add`。

`--weight N` 只在 add 模式生效：一个池里列几条荧。默认 1 条 —— 池里原本 3 个候选时
占 1/4；`--weight 2` 就是 2/5。

产物 `content.xml` + `ext_01.cat` + `ext_01.dat` 放进
`X4 Foundations/extensions/x4_lumine_mod/`。

## 文档

- [`docs/荧移植进展.md`](docs/荧移植进展.md) —— 完整工程日志：目标种族侦查、
  修复过的每个真 bug（UV v 轴、alpha 渗漏、脖子折角、重合层频闪、导出器硬编码
  shader）、**已知问题**（关节残余撕裂，含尝试与回退记录）、以及一长串
  "诊断脚本自己出错"的复盘。

## 已验证

| 项 | 结果 |
|---|---|
| 骨架 | 91/91 bind payload 逐字节相同 |
| 骨骼映射 | 210 根带权骨 → 53 直接 + 157 折叠 + 0 未映射 |
| 导出顶点 | head 4813（vanilla 4693）/ body 11325（vanilla 3601）|
| 贴图 | 29/29 带完整 mip 链 |
| 发版自检 | `verify_mod.py` 全过（参数与产物形态一致时）|

## 已知问题

**关节处的残余撕裂**（脚腕、肩臂、手肘）。根因是源骨架与 X4 骨架的脊柱/腿长比例
不同，而"给骨链共享位移"的修法会引入更明显的弯折，已回退。详见文档 §3.12。

## v1.4 修了什么

**走路像猫步、坐姿两脚贴得很近。** 猫步的判据是**步态宽度**——vanilla 女性
走路时两脚相距 39.8 cm，而阻尼过强的版本只剩 18.0 cm，比骨盆（23 cm）还窄，
于是每一步都跨过中线。修法是让脚部保留几乎全部横向行程
（大腿 0.60 / 小腿 0.85 / 脚 0.95）：

| 指标 | v1.2 | v1.3（不够） | **v1.4** | vanilla |
|---|---|---|---|---|
| 两脚间距（几何中心） | 18.0 cm | 30.5 cm | **35.9 cm** | 39.8 cm |
| 脚踝骨 vs 脚部几何 | 7.06 cm | 2.47 cm | **0.28 cm** | — |

骨架、父子链、局部坐标系都与 vanilla 逐值相同（旋转差 <1e-6 度），所以动作
本身不变形——问题只在宽度。详见文档 §九。

## 版本与文件

发布包由工作区的 `work/build_release.py` 统一生成，文件名写清配置：

```
x4_lumine_terran_add_v1.4.zip      泰伦/先驱者女性 · 加入外观池（推荐）
x4_lumine_terran_replace_v1.4.zip  泰伦女性 · 全部替换（含剧情 NPC）
x4_lumine_argon_add_v1.4.zip       阿贡女性 · 加入外观池
```

## 版权

模型版权归 miHoYo；模型改造者是 **观海（Bilibili：观海子）**，其为二次创作。本仓库**只包含工具与文档**，
不含模型、贴图或游戏资产。
