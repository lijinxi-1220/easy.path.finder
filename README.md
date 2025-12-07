# Easy Path Finder - 后端工程概览

本工程基于 Django + Vercel Serverless，提供用户认证、简历解析与优化、岗位/院校匹配、职业规划、AI 对话、增值服务、用户数据与进度等接口。所有接口均使用统一的认证、错误响应、限流与校验规范。

## 统一规范
- 认证：`Authorization: Bearer <JWT>`；`sub` 为用户标识；退出使用 `jti` 黑名单
- 请求标识：中间件自动注入 `X-Request-ID` 响应头；访问日志结构化输出（含 `request_id`、耗时、用户）
- 错误响应：`{ code: <int>, error: <string> }`
  - 业务错误统一抛出 `BusinessError(code, message, status)`，中间件映射为错误响应
  - 常见错误码：`1001` 用户名存在、`1002` 参数无效/缺失、`1010` token 无效、`1011` token 过期、`1020` 频率限制
- 速率限制与幂等：
  - 登录：每 IP `10/min`
  - 发送验证码：每 IP `5/min`，并叠加用户级 60s 节流
  - 咨询申请：每用户 `3/hour`；支持头 `Idempotency-Key` 防重复
  - 注册、订阅：支持头 `Idempotency-Key` 防重复
- 参数/体校验：
  - `validate_query` 支持 `int|str|bool|date|iso-datetime`、`min|enum|required|default`；统一分页与排序参数
  - `validate_body` 校验 POST/PUT JSON 请求体；失败返回 `1002` 参数无效

## 模块与仓储层
- users：用户认证与资料；仓储 `users/repo.py`
- resumes：上传解析、评分、优化、管理导出；仓储 `resumes/repo.py`
- matches：岗位画像、匹配分析、推荐、院校详情；仓储 `matches/repo.py`
- plans：目标/任务/规划书/动态调整；仓储 `plans/repo.py`
- chat：对话交互、引导、历史、消息分页；仓储 `chat/repo.py`
- userdata：隐私设置、历史查询、进度数据；仓储 `userdata/repo.py`
- services：课程/实习推荐、导师列表与咨询、项目推荐、会员订阅；仓储 `services/repo.py`
- 核心横向能力：`core/*`（middleware、logger、validators、ratelimit、security、idempotency）

## 文档入口
- 用户接口：`users/README.md`
- 简历接口：`resumes/README.md`
- 匹配接口：`matches/README.md`
- 规划接口：`plans/README.md`
- 对话接口：`chat/README.md`
- 用户数据与进度：`userdata/README.md`
- 增值服务：`services/README.md`
- OpenAPI 初版：`openapi.yaml`

## 部署提示
- 配置优先使用模块本地 `config.py`；可通过环境变量覆盖（前缀 `EASY_PATH_*`）
- 为 Serverless 环境设置必要的 Upstash Redis 连接与 JWT 密钥；确保日志与错误码规范符合监控系统

