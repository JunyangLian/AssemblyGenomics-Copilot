# v2 阶段3运行说明

只使用冻结的24题。命令在本地仓库根目录运行，Python环境需已有jsonschema和PyYAML。

```powershell
python bench/v2/plan.py --create
python bench/v2/run.py --mode mock
python bench/v2/mock_report.py
python bench/v2/import_rules.py --reuse
python bench/v2/rules_package.py
```

plan --create为首次锁定，已有计划时只验证，不覆盖。RUN_PLAN保护本版运行代码、共用纯函数、模型提议配置、公共文件、原规则及48条A复用身份。答案和分析规格仍由原FROZEN保护；运行代码不加入或改写它。C2为所有模型共用的一套冻结内容，C2相对B只增加知识包；相同材料、schema、参数和重复数。模型输入通过visible_input.packet白名单构建，不包含expected/meta/labels或审查材料；固定schema提及禁止的私有文件名不代表载入其内容。请求摘要哈希可结合冻结公共材料和锁定代码重建请求。

mock固定seed=20261007，随机合法JSON。A的72条仅运输模拟，status=execution_error、parsed=null、simulated=true，不能计为规则成功或真实QC能力；48条v1真实A单独核对规则、映射、输入字节及packet身份后复用，不新增执行。规则覆盖只代表日志列出的检查范围；已有适配层可能对任务中的参考FASTA也检查小写比例，或执行蛋白字符检查而未覆盖功能质量。这些限制保留用于评测，不添加生物学规则迎合新题。

每个模型/组保存一个runs目录；run_id为时间戳、模型名、组及FROZEN.md哈希前缀。JSONL含原始响应（脱敏）、请求摘要、解析结果、供应商usage或null、耗时、重复与attempt。一次格式修复重新发送同一材料+通用修复提示，不传上轮模型内容、评分反馈或答案。再次解析失败保留parse_error；网络错误不重试。模型型号明确不同则保留identity_error并暂停该模型剩余槽位。其它未调用/失败槽位保留，不缩小计分分母。

阶段3mock不计算H1–H3。阶段4才能根据冻结预注册计分，主要按题独立形成verdict/root多数，重复作为次要观测；人工action盲编码与自报flag分开。

真实API入口为python bench/v2/run.py --mode api，目前会拒绝。API_APPROVAL.template.json不是许可，所有数值及确认留空；后续依据用户明确批准写独立API_APPROVAL.json，绑定运行计划、冻结哈希与mock报告。需要调用次数、输入/输出规划预留上限及对未知费用/思考模式的确认。key只从本地INTERN_DISCOVERY_API_KEY读取；mock不读key。仅OpenAI Chat Completions，HTTPS、禁止重定向、超时300秒、响应上限16MiB，无隐式重试。temp=0、max_tokens=8192是请求值，实际值未报告时为unknown。

v2账本固定runs/API_LEDGER.json，预留在每次请求前写入，包括格式修复；不释放未知用量，不因新运行计划清空旧额，也不读取/重置v1的账本。达到批准上限或usage超过规划预留则阻止继续调用。并发live运行通过排他锁禁止；中断留下锁/预留时须先审查，不能盲目删除重跑。当前入口不自动恢复中断槽位，已有预留重复请求会拒绝。费用未知不能保证货币上限，token规划开销也不是平台计费的数学上界。

服务器只上传v2/rules_package.zip，放到~/AssemblyGenomics-Skill/bench/v2/。在服务器bench下：

```bash
python -m zipfile -e v2/rules_package.zip v2/rules_package
python v2/rules_package/server/run_rules.py
```

包内只有8题公共材料、原18个规则注册/脚本文件、原适配层与运输工具及服务器入口，0 API，无模型配置/key/expected/meta。原规则按CRLF→LF归一后固定，不改逻辑；直接从包内original_rules运行，避免依赖服务器仓库原目录。输出固定bench_transfer/v2_rules_run_1/bundle，重复执行覆盖已知输出文件、不追加旧行；检查工具版本、结尾摘要及完整SHA-256清单。只验包内小文件，不扫描原始来源。

scp回传bundle整目录后，在本地运行python bench/v2/import_rules.py <bundle目录>。验收运输清单、24个新A槽位、公共输入与规则/适配身份、结构化输出及计数，保存新增运行并与48条真实复用合成72条A入口记录。mock A和单元测试的服务器演练不得作为这个真实A回传。

平台公开页：https://discovery.intern-ai.org.cn/token-plan/home。无五模型计费权重，按用户回复“没有，先看 token 估算”仅给代理和字节规划上界；不套原厂价格。当前止于mock与报告，等待阶段3批准。

2026-10-07用户随后回复“确认，继续开启”：API_APPROVAL.json已采用报告全修复情景的1440调用/28706760输入预留/11796480输出预留上限，绑定mock及运行锁。启动检查发现本地进程与用户环境都没有INTERN_DISCOVERY_API_KEY，真实请求仍0；当前待设置环境变量。用set_api_key.ps1的隐藏提示在本机输入，再由agent启动正式runner；聊天中的凭据不复制到命令、文件或日志。证明见API_START_REPORT.md及API_START_STATUS.json。

后续用户要求agent直接设置，已用隐藏输入设置本机用户环境，正式入口现在为powershell -NoProfile -ExecutionPolicy Bypass -File .\bench\v2\start_api.ps1。它读取本地环境并仅为授权平台添加进程范围NO_PROXY，结束时恢复；该域名的本地代理TLS已证实失败，证书校验不降低。当前v2-run-3采用官方小写请求ID，原展示名、题目、参数和分析不改。前两次失败队列保留720+720全部计划槽位及451次预留，累计预算不增加。来源/修订/暂停Flash的原因见API_START_REPORT，进度命令python bench/v2/api_progress.py不读取key，也不计分。

当前rules_package.zip绑定v2-run-3，请使用当前包传服务器。任务与规则本身不改，输出位置/命令仍相同；旧包只归档、不用来覆盖当前包。规则结果回传仍须严格核对身份，mock和基础设施诊断不当作真实A。

2026-10-07 用户纠正名单：v2-run-4 的官方请求 ID 为 deepseek-v4-flash-0731、deepseek-v4-pro-0813、minimax-m3、glm-5.3、qwen3.8-27b。GLM 替换 Kimi；官方只读元数据另存 PROVIDER_MODELS_ROSTER2.json。原冻结名单和答案不覆盖，运行后修订的时间顺序及分析影响见 PREREGISTRATION_AMENDMENT_20261007.md。

续跑由 resume.py 读取锁定的 history/v2-run-3/RESUME_RECEIPT 与原始记录；98 条已有观测（含 24 条有效 Pro、超时、中断和 Flash 暂停）全部原样承接。API_RUNS.json 在请求前固定唯一目录索引，再运行使用原目录并跳过所有已完成槽位。账本已预留但无最终结果的请求记 interrupted，不补发；保留 identity_error 引起的跨组暂停。父计划同一语义槽位的重复预留也会拒绝。禁止依据标准答案选择补跑；标准答案不用于恢复判断。

启动命令仍为 powershell -NoProfile -ExecutionPolicy Bypass -File .\bench\v2\start_api.ps1。本地环境 key 无需重设；统一预算上限不扩充。当前 A 包绑定 v2-run-4，服务器操作与回传目录不变。费用/账户墨点尚未确认；官方模型元数据的 pricing 仅是平台公布值，不能冒充余额或实际账单。

用户随后选择 deepseek-v4-flash-vision，当前锁为v2-run-5。Vision作为替换型号新跑144槽位，原0731错误/暂停保留审计，不改为成功或拿其响应冒充Vision。Pro等其它模型所有既有好/坏结果均承接；原题库、提示、参数、分析门槛不变。三个允许返回标识仅对Vision生效（官方ID、展示名、用户已知并选择的dsv4-flash-vision），不是开放别名或证明0731权重，详情见新预注册附录。

累计预算不增加；API_START_STATUS的执行调用与承接调用分列。未来需停队时创建bench/v2/runs/STOP_AFTER_CURRENT_REQUEST，当前观测完成后返回而不生成未执行槽位的伪失败；resume目录索引保持不变。清除标记前须确认旧进程退出；保留所有未知预留。当前A ZIP绑定v2-run-5，规则/输入不变，仅运行锁身份更新。

用户随后要求四个同时运行，当前v2-run-6启用最多四个请求线程、每模型最多一个在途观测，以模型轮转队列分配名额。每模型内部B后C2；全局不再等所有B结束才进入C2。同一观测的格式重试在原线程顺序执行；网络失败仍不重试，身份错误只暂停对应模型并保留槽位。其它模型继续，因此慢请求不会占住所有名额。

ConcurrentBudget在共享互斥锁内重新读取同一API_LEDGER，检查祖先/当前槽位防重复、累计调用和token上限，原子替换完整账本后才能POST。usage同样在锁内更新，不能覆盖另一线程的预留/usage；超出规划用量阻止随后新预留，已经在途的最多四请求等待结束。Windows临时共享错误采用有限重试，损坏JSON仍报错。独占进程锁不取消，不启动四个独立runner。

旧75条观测与527次预留全部承接，平缓切换未新增中断；新主体题尚未观察，调度修订登记SCHEDULING_REVISION。实际运行信息在runs/SCHEDULER_STATUS及API_START_STATUS.concurrency，包括最多/峰值线程、在途题目和等待数。若创建STOP_AFTER_CURRENT_REQUEST，将停止派发并等待所有已在途观测结束，不伪造剩余失败；正式恢复前清除这个已审核标记。入口命令仍start_api.ps1，无需重新设置key或批准预算。
## 当前执行版本 v2-run-7（2026-10-08）

六模型六线程，每模型最多一个在途观测，共864模型槽位。用户接受Qwen FP8并要求独立标注；新FP8与Kimi各144槽位，旧Qwen144条身份错误/暂停留在历史审计。其它四模型85条承接。register_six登记授权、名单附录、官方映射及新运行锁，revision_snapshot在旧队列平缓停止后归档。

六并发继续共用原累计预算与互斥账本，不启动六个独立runner、不重发旧成功或失败槽位。六模型全格式修复情景1728次高于原1440次上限，实际以累计余额为准。启动前新mock须864条全部通过并绑定API_APPROVAL；API key仍只读本地环境。最新动态状态见API_START_STATUS，预注册数字阈值不变而模型分母变化另行披露。
## 当前执行版本 v2-run-8：第二凭据恢复

用户明确批准623条最终HTTP429恢复和所需新累计预算。credential_recovery.py只按运输错误筛选，不读取答案/正确性；register_credential_recovery登记父864记录、623恢复槽位、241承接观测、授权和公开请求推算的上限。resume跳过登记的旧429槽位，让runner重新执行，原失败永远留在父历史；ConcurrentBudget仅允许这些槽位的父429预留重试，当前版本重复预留与其它父槽位仍拒绝。

累计上限2636/52724811/21594112包含原1390次预留；key只从本机环境读取，不按新key重置账本。模型、提示、温度、输出限额、重复数、答案及C2不改；仍六并发。新429触发停止派发、等待在途结束并保留待运行槽位。原始运行与恢复队列分别报告，统计分母864，不删错误或伪造新独立重复。
## 当前执行版本 v2-run-9：第三凭据、四模型优先

execution.active_model_names仅含Vision、Pro、MiniMax、Qwen FP8，max_workers=4；GLM/Kimi仍在配置、历史和目录索引，API队列为空，不创建客户端。375条父观测承接（含暂停模型70条），271条登记的429恢复机会派发。第三key只读本机环境，原1578次预留不退还、累计2636/52724811/21594112上限不增加。

priority_candidates核对原v2-run-7完整429来源及v2-run-8最终观测，只开放优先四模型的未尝试原429与最新429。重复预留豁免逐槽位登记祖先版本，当前v2-run-9重复始终禁止；已有超时、502、解析错误与有效结果不重跑。四模型576完成状态与六模型864整体完成分开，不删暂停分母。原始/恢复日志分别报告，冻结材料和数字门槛不变。
