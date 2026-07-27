# Workflow Preset

`workflow-preset` 是一个 Spec Kit 社区预设（community preset），把需求、
架构、设计、测试条件与任务映射成一条可审计的 SDD（Specification-Driven
Development，规格驱动开发）链路。

它不提供或替换 `/speckit.implement`。实现执行始终由当前安装的 Spec Kit
core（核心命令）负责。

## 命令所有权

| 命令 | 本预设的职责 | 写入边界 |
|---|---|---|
| `/speckit.constitution` | 分离治理规则与仓库技术架构 | `constitution.md`、`architecture.md` |
| `/speckit.specify` | 编写完整 WHAT/WHY 需求 | `spec.md` |
| `/speckit.clarify` | 按影响 × 不确定性消除产品歧义 | 仅 `spec.md` |
| `/speckit.checklist` | 用问题形式检查需求写作质量 | `checklists/*.md` |
| `/speckit.plan` | 在 Core Plan 生命周期内完成 X0–X4 | Plan 设计产物 |
| `/speckit.tasks` | 把已批准的 Plan 记录映射成可执行任务 | 仅 `tasks.md` |
| `/speckit.analyze` | 只读审计跨命令追踪链 | 不写文件 |
| `/speckit.implement` | 由 Spec Kit core 执行 `tasks.md` | 本预设无覆盖 |

## 生命周期

```text
Constitution + Architecture
            ↓
     Spec → Clarify → Checklist
            ↓
   Core Plan（内含 X0–X4）
            ↓
 Tasks（T0–T5 纯映射）
            ↓
   Core Implement
```

### 需求层

授权来源投影完成后，`spec.md` 是当前功能的产品需求唯一事实源（SSOT,
Single Source of Truth）。功能需求、非功能需求、UX/UI、视觉、安全隐私、
数据、集成、依赖、边界、假设和排除项都使用可选载体；不适用时明确写
N/A。

`/speckit.specify` 与 `/speckit.clarify` 不生成或修改 checklist。
`/speckit.checklist` 只提出可回答的问题，不把实现方案写回需求。

例如：退款需求可以同时声明 `FR-001`（退款规则）、`NFR-001`（响应时间）和
`UI-001`（加载/成功/失败状态）；若已授权的设计说明缺少结账失败态证据，
就在对应 `SRC-*` 行记录本地阻塞，不把它混成产品澄清问题。

### 来源中立契约

自然语言、需求文档、可执行视觉引用和技术证据统一进入现有
Source Reference Contract（来源引用契约）：

```text
SRC ref | role | opaque locator/description | revision/identity
| authorized scope/facts | projected requirement refs | status/blocker
```

| 角色 | 含义 | 例子 |
|---|---|---|
| `requirement-input` | 可投影已确认、已切片的 WHAT/WHY | 当前对话中的退款规则 |
| `visual-input` | 只可投影 `UI-*` / `VIS-*` | 结账错误态的可执行页面引用 |
| `technical-evidence` | 可引用，但不升级成产品需求 | 性能测量报告 |
| `context-only` | 只作背景，不授权规范性事实 | 竞品介绍 |

定位符（locator）、路径、版本、摘要或文字描述都按不透明来源信息保存。
预设不会因为看到一个引用就打开、执行或验证它，也不会推断相邻目录或要求
上游工具。宽泛来源必须先确定当前功能切片；无法安全切片时只记录本地阻塞
或待澄清项，不默认整份导入。

本地链路是：

```text
SRC-* + 本地需求
        ↓
spec.md（本功能 WHAT/WHY SSOT）
        ↓
X2-B: ui-ux-design.md → UIF
        ↓
Tasks 只做实现映射；Analyze 只做本地引用审计
```

### Plan：X0–X4

X0–X4 是嵌套在原有 Core Plan 流程中的内部里程碑，不替换 Core 的 setup、
Phase 0、Phase 1 或 Constitution re-check。

| 里程碑 | 目标 | 主要产物 |
|---|---|---|
| X0 | 输入、门禁和架构修订对齐 | `plan.md` |
| X1 | 研究并关闭技术/验证未知项 | `research.md` |
| X2-A | 领域、对象和接口设计 | `data-model.md`、`contracts/`，按需生成 class/sequence |
| X2-B | UI/UX 交付就绪设计 | `ui-ux-design.md` |
| X2-C | 测试与验收设计 | `contracts/test/test-conditions.json` 及可选技术子契约 |
| X3 | 定义可执行验证路径 | `quickstart.md` 中的 `VAL-*` |
| X4 | 汇总测试/任务交接 | `test-readiness.md`、`PLAN_OUTPUT_READY` |

`contracts/test/test-conditions.json` 是测试条件父契约。BDD、场景、fixture
（测试数据）和 assertion（断言）只有在技术适用时才生成；非 UI 功能和
无 fixture 场景可以记录明确理由。

UI/UX 像素级交付准备可以在 Plan 中完成，但 Tasks 不得生成像素还原、
截图对比、visual diff（视觉差异）、baseline（基线）、视觉恢复或渲染审查
任务。

### Tasks 与 Analyze

`/speckit.tasks` 只消费 `PLAN_OUTPUT_READY`，按 T0–T5 映射已存在的设计对象、
路径、依赖、测试条件和 `VAL-*`。必需的 `TC-*` 会覆盖 Core 模板中“测试可选”
的默认提示；最后一个强制阶段始终是 **Final Code Review**。

`/speckit.analyze` 一次读取 Constitution、Architecture、Spec、Plan 与 Tasks，
输出稳定 finding ID、严重级别、证据和第一个阻塞点。它负责检查
Architecture → Plan、Plan → Tasks、M + U 范围，以及数据模型的幂等、提供方
绑定、重试、恢复和生命周期投影；同时检查 `SRC-*` 的本地存在性、角色和
X2-B/UIF 投影。它不会访问外部定位符、修文件或发明新的 Plan 策略。

## 安装

开发目录：

```bash
specify preset add --dev /path/to/spec-kit-workflow-preset
```

已发布版本：

```bash
specify preset add --from https://github.com/bigsmartben/spec-kit-workflow-preset/releases/download/v3.1.0/spec-kit-workflow-preset-v3.1.0.zip
```

安装后可检查预设信息：

```bash
specify preset info workflow-preset
```

## 开发与验证

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest tests/test_preset_contract.py
```

扩展规则见
[`docs/extension-governance.md`](docs/extension-governance.md)。发布产物必须
记录源仓库、版本、source commit SHA、下载地址、压缩包 SHA-256 和逐文件
哈希；下游集成先进入 `bigsmartben/spec-kit`，不得从本仓库直接写入
`github/spec-kit`。
