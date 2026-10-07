# v2 正式运行授权与启动状态

2026-10-07，用户在阶段3汇报后回复“确认，继续开启”。五模型、24题、B/C2、每题3次、最多一次格式修复及未知价格/默认思考的限制沿用已审阅报告；API_APPROVAL.json绑定原运行锁、答案冻结与mock报告。

采用报告中全格式修复情景的规划上限：max_calls=1440、max_input_tokens=28706760、max_output_tokens=11796480。初始请求仍720次；不增加题目、重复或网络重试。未知费用不能据此保证货币上限，服务端隐藏资源也不等同字节规划预留。没有修改答案、C2、预注册、原适配实现或v1账本。

启动前检查：当前进程及Windows用户环境中INTERN_DISCOVERY_API_KEY都未设置，因此还没有真实API请求、预留或响应。不会把聊天凭据复制到脚本、命令参数、仓库或日志。当前状态为waiting_for_key_environment，不能报告正式运行已开始。

在本地PowerShell的仓库根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bench\v2\set_api_key.ps1
```

按隐藏提示输入平台key。脚本只设置本地用户环境变量，不显示内容、不记录凭据、不调用API；输入不出现在命令历史中。设置完成后回复“已设置”，agent从用户环境继承到启动进程，再执行已批准的run.py --mode api。服务器不接收key或B/C2配置。

完整pytest：278 passed in 82.54s (0:01:22)。PowerShell隐藏输入脚本语法校验通过，批准文件和v2冻结运行锁验证通过。正式结果仍待本地凭据；新增A24条仍待服务器包回传。当前不进入阶段4计分。
