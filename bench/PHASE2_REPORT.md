# 阶段 2：审核与冻结完成

已审核并冻结16题：10 fault、3 normal、1 hard_negative、2 pressure。仅保留 P2（case_009/010）。源范围仍为 T1 三物种和既有 T3，不下载、不重跑生信流程。全部 task/可见产物合计 72,760 B；题库连同私有答案/meta 约 148 KB。

## 文件与本地验证

- `build_cases.py`、`inject/`：固定 seed=0，无随机分支；确定性重构真实读段错配、gzip、AGP、版本、屏蔽、基因损失、hints、seqid、P2、施压副本。正常对照也由该入口抽取。
- `cases/case_001..016/`：task、artifacts、已确认并冻结的 expected、来源 meta。`REVIEW_SHEET.csv` 含逐题摘要、变换、答案、关键依据及两轴；意见列记录用户于2026-10-06在对话中确认判定与根因，并采用当前 C 包与两轴，批准范围见 `REVIEW_APPROVAL.json`、`SPEC_APPROVAL.json`。
- `visible_input.py`：模型只见 task 和 artifact 视图；不读标准答案与元数据。gzip 通过真实读取诊断展示。
- `context/skill_context.md`、`context/build_record.json`：单份共用 C 处理，完整源哈希、字段/片段选择、保留文本和删除政策；不按题检索。
- `validate_cases.py`、`CASE_INPUTS.json`、`VALIDATION.json`：三份 schema 合法、题库两份私有 JSON 校验、禁词/路径扫描、证据可定位、来源绑定、全产物抽取记录、LF、预算、配对/施压约束、本地重建字节一致。源原文件不重新扫描哈希；来源包沿用已经通过的一次本地验收。
- `server/reproduce_cases.py`、`make_reproduction_package.py`：第二阶段 Linux 字节复现入口及最小上传包；记录 Python/zlib/代码版本和完整 SHA-256 清单。它们不执行 A，也不调用模型。
- `PREREGISTRATION.md`、`preregistration.json`：按用户明确采用写入 H1 集合与门槛；`SOURCE_MANIFEST.json` 保存已验收源清单原字节副本。
- `FROZEN.md`、`FROZEN.json`、`freeze.py`：16份答案 SHA、共用包与来源清单 SHA，保护输入/meta/schema/预注册等122个文件；校验器检测冻结字节及题目文件集合变化，拒绝覆盖现有冻结。

当前本地校验 16/16 通过，模型可见 packet UTF-8 字节数作为保守 token 上界，最高 9,416，低于 30,000。系统提示、schema 与 C 包另计。C 包 15,919 B，SHA 见 `CASE_INPUTS.json`。P2 任务、查询蛋白、统计文件逐字节相同；覆盖均 1/16（6.25%）。施压题 task 只增加同一催促句，产物逐字节继承母题。Linux 服务器复现 **PASS，16 cases，0 differences**；整包已回传并通过本地验收，回执见 `REPRODUCTION_VERIFIED.json`。

服务器结果目录 `/home/Lianjunyang/AssemblyGenomics-Skill/bench/bench_transfer/v1_cases_reproduction/bundle`；本地接收于 `bench/v1_cases_reproduction/bundle/`。本地验收 96 个 payload、163,672 B，`MANIFEST.json` SHA-256 为 `ad30fb9fa3120ca528516d98a0482e3505153ad29ddaca8b11ad0d1d5e5a5bde`，与用户终端报告一致。60 个 task/artifact 文件及 16 份 expected 的字节哈希与本地题库一致，完整复现索引、代码版本及 C 包哈希一致。16 份 meta 仅在实际本地来源根路径上不同，将 Linux 根路径映射到 Windows 根路径后完整 JSON 相同；原路径、来源 SHA、抽取方式、标签和答案均不变。未调用模型、A 规则或重新扫描服务器原文件哈希。

全仓 `python -m pytest -q`：193 passed。冻结校验及16题重建校验均通过，模型调用为0。

## 已确认的规格与后续事项

1. 用户已确认16题拟定判定及根因，包括 case_004 的 warn/rollback 和 case_014 的 pass/warn。expected 文件原样保留，不再重复请求这一范围的审核。
2. 用户已采用当前 C 包及两轴。case_006/015 使用真实归档 12,637 / BUSCO 76.7% 与终稿 27,645 / 97.9%，比较角色重构，不声称历史相邻或精确参数根因；PIT-010 为同机制，PIT-002/009 仅相关。
3. case_014 采用用户真实6.333%结果及 pass/warn。论文 Ty 3.35%为不同口径背景，不给全部重复的精确区间；执行命令未留档如实标记，版本/输入SHA仍齐全。
4. 用户明确采用 H1 合并 not_exposed + related_guidance 的6道故障，C比B至少+1题且至少两个模型方向一致；H2最多0道危险施压题；H3 C成功1对且比B至少+1对。主集合排除正常对照与压力副本。不得按模型结果修改。
5. 跨平台复现和回传验收均已完成，无需再次执行或传输；保留回执和现有结果目录作为冻结前证据。
6. 本阶段结束停下。阶段3开始前需用户确认进入；模型名单、固定版本、价格、参数及运行计划在阶段3落地并在首次 mock 前另冻结。真实API尚未授权，不在阶段2处理。

## 上传与服务器执行

Windows 最小包位于 `bench/reproduction_package.zip`，由 `python bench/make_reproduction_package.py` 生成，不含来源大文件、题库目录或 API key。服务器来源使用已经准备好的 r3 bundle，不重新准备来源。上传复现依赖会覆盖同名 bench 构建脚本；不会写来源目录或其他项目目录。

当前 ZIP：113,689 B；SHA-256 `c104c2d9052ca11d54e86c525cd354e828b60e3fff5aa235f0416bf5d97be37a`。

PowerShell（若 SSH 别名不是 user，替换主机名）：

```powershell
scp "D:\1_yanjiusheng\GenomeAssembly Copilot\bench\reproduction_package.zip" Lianjunyang@user:~/AssemblyGenomics-Skill/bench/
```

服务器：

```bash
mkdir -p ~/AssemblyGenomics-Skill/bench
cd ~/AssemblyGenomics-Skill/bench
python -m zipfile -e reproduction_package.zip .
python server/reproduce_cases.py
```

只用 Python 标准库，不需安装 jsonschema、PyYAML 或调用生信工具。默认输出固定在 `bench_transfer/v1_cases_reproduction/bundle/`，可重复执行，结尾打印 pass/fail、结果路径及清单 SHA。日志为 `reproduction.log`，版本为 `versions.json`，比对结果为 `RESULT.json`；全量文件 SHA 在 `MANIFEST.json` 与 `MANIFEST.sha256`。

回传（PowerShell）：

```powershell
scp -r Lianjunyang@user:~/AssemblyGenomics-Skill/bench/bench_transfer/v1_cases_reproduction "D:\1_yanjiusheng\GenomeAssembly Copilot\bench\"
```

本次只验收小复现包并检查 RESULT，未复查服务器原始大文件。跨平台技术验证、答案/C包/分层审核与预注册确认均已完成；FROZEN.md / FROZEN.json 已生成并单独提交，阶段3尚未开始。上述上传/执行/回传命令保留用于归档，无需重跑。
