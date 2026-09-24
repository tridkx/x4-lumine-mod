# 荧（原神）→ X4: Foundations **Terran 女性** NPC

把《原神》女主角**荧**的模型移植成《X4：基石》里**所有 Terran 种族女性 NPC** 的外观，
完全替换她们的头部与躯干网格。

这是本工作区的**第三个** X4 角色 mod。管线骨架沿用
[`x4-character-retarget`](https://github.com/tridkx/x4-character-retarget)
（萝丝 → X4 Argon），但**目标种族换了（Argon → Terran）**，
按 skill 的要求把每一处都重新量了一遍。

## 与另外两个项目的关键差异

| | 萝丝 / 艾梅莉埃 | 荧 |
|---|---|---|
| 目标 | Argon 女性 | **Terran 女性** |
| 替换方式 | 改外观池（charactergroups） | **逐个 macro 覆盖 `<models>`** |
| 覆盖范围 | 池内随机 NPC | 45 个 macro（含剧情 NPC） |

**Terran 女性与 Argon 女性共用同一个 component**（`character_argon_female_01`），
所以骨架、动画、host 模板全部复用；但**每个 Terran 派生 macro 都重写自己的
`<models>`**，改 base 无效，必须逐个 macro 替换 —— 这也顺带覆盖了不经过外观池的
剧情 NPC，并保留了 NPC 身份的多样性。

## 复现

```bash
python   tools/find_terran_female_macros.py                      # 生成 45 个 macro 清单
python   tools/prepare_textures_lumine.py                        # 贴图 → DDS + manifest
blender -b --factory-startup --python tools/build_lumine_x4.py    # 阶段1：重定向
blender -b --factory-startup --python tools/build_lumine_mod.py   # 阶段2：导出 .xac
python   tools/make_mod.py                                        # 组装 mod 树
XRCatTool.exe -in work/x4_lumine_mod -out work/x4_lumine_mod/ext_01.cat
python   tools/verify_mod.py                                      # 发版自检
```

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
| 发版自检 | `verify_mod.py` 全过 |

## 已知问题

**关节处的残余撕裂**（脚腕、肩臂、手肘）。根因是源骨架与 X4 骨架的脊柱/腿长比例
不同，而"给骨链共享位移"的修法会引入更明显的弯折，已回退。详见文档 §3.12。

## 版权

模型版权归 miHoYo，模型改造归原作者（观白）。本仓库**只包含工具与文档**，
不含模型、贴图或游戏资产。
