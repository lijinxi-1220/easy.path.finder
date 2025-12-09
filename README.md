# Easy Path Finder - 后端工程概览

本工程基于 Django + Serverless，提供用户认证、简历解析、岗位/院校匹配、职业规划、AI 对话、增值服务、用户数据与进度等接口。所有接口统一认证、统一错误、统一分页/校验，前端可按本文档快速接入与校验。

## 统一规范
- 认证：`Authorization: Bearer <JWT>`（除注册、登录、发送验证码外）；JWT `sub` 为用户标识。
- 错误：统一返回 `{ code, error }`；服务端使用 `BusinessError(code, message, status)`。
- 分页：`page`（默认 1）、`page_size`（默认 20）；响应含 `meta.total|page|page_size`。
- 速率限制与幂等：登录 10/min（按 IP）、验证码发送 5/min（按 IP）+ 60s 用户节流；咨询 3/h（按用户）；注册/订阅支持 `Idempotency-Key`。
- 校验：`validate_query`/`validate_body` 统一参数校验；非法返回 `{ code: 1002, error: 'invalid_param|invalid_json' }`。

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
 - 统一 IDL 速查：`docs/API.md`

## 快速校验（cURL）

以下命令可快速验证主要模块连通性；默认服务地址 `http://localhost:8000`。

### 1. 注册与登录
```bash
curl -s -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123","email":"a@x.com","phone_number":"123"}'

TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .token)
USER=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .user_id)
```

### 2. 用户资料（读/改）
```bash
curl -s http://localhost:8000/profile/$USER -H "Authorization: Bearer $TOKEN"
curl -s -X PUT http://localhost:8000/profile/$USER \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"full_name":"Alice","gender":"F"}'
```

### 3. 简历上传与评分/优化
```bash
RID=$(curl -s -X POST http://localhost:8000/resume/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F resume_name="My Resume" -F resume_file=@./resume.docx \
  -F skills='["Python","Django"]' | jq -r .resume_id)

curl -s "http://localhost:8000/resume/score?resume_id=$RID" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/resume/optimize?resume_id=$RID&target_job=Backend" -H "Authorization: Bearer $TOKEN"
```

### 4. 规划：目标与任务（含 POST action）
```bash
# 创建目标
GID=$(curl -s -X POST http://localhost:8000/plan/goals \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"goal_name":"Offer in 3 months","target_date":"2026-01-01"}' | jq -r .goal_id)

# 列表（GET）
curl -s "http://localhost:8000/plan/goals?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"

# 列表（POST action=list）
curl -s -X POST http://localhost:8000/plan/goals \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"list","status":"active","page":1,"page_size":10}'

# 生成任务（POST action=generate）
curl -s -X POST http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"generate","goal_id":"'$GID'"}'

# 任务列表与更新
curl -s "http://localhost:8000/plan/tasks?goal_id=$GID&page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
TID=$(curl -s -X POST http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"goal_id":"'$GID'","task_name":"完善技能清单"}' | jq -r .task_id)
curl -s -X PUT http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"task_id":"'$TID'","status":"done"}'
```

### 5. 匹配：岗位画像/分析/推荐
```bash
# 画像导入（管理员）
ADMIN=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .user_id)
ADMIN_TOKEN=$(python3 - <<'PY'
from users.api.auth import issue_jwt
import os
print(issue_jwt(os.environ.get('ADMIN'), 'admin', 'admin'))
PY
)
curl -s -X POST http://localhost:8000/match/admin/job_profiles/import \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '[{"job_profile_id":"job-1","job_title":"Software Engineer","company":"Example","required_skills":["Python"],"required_experience":"2+ years","industry":"software"}]'

curl -s "http://localhost:8000/match/job_profile?job_title=Software%20Engineer" -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/match/analysis \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"resume_id":"'$RID'","target_type":"job","target_id":"job-1"}'
curl -s "http://localhost:8000/match/recommend?preference=both" -H "Authorization: Bearer $TOKEN"
```

### 6. 对话：交互/历史/消息
```bash
CID=$(curl -s -X POST http://localhost:8000/chat/interact \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"message_content":"请帮我看看简历","chat_scene":"resume"}' | jq -r .chat_id)
curl -s -X POST http://localhost:8000/chat/interact \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"message_content":"继续","chat_scene":"resume","chat_id":"'$CID'"}'
curl -s "http://localhost:8000/chat/history?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/chat/messages?chat_id=$CID&page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
```

### 7. 增值服务：推荐/导师/咨询/项目/订阅
```bash
curl -s "http://localhost:8000/service/recommend?service_type=course&page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/service/mentors?field=backend&sort_by=years&sort_order=desc" -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/service/consult \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -H 'Idempotency-Key: req-123' \
  -d '{"mentor_id":"m1","consult_topic":"topic","consult_time":"2026-01-01T00:00:00Z"}'
curl -s "http://localhost:8000/service/projects?project_type=exchange" -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/service/subscription \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -H 'Idempotency-Key: req-456' \
  -d '{"subscription_type":"month","payment_info":{"channel":"mock"}}'
```

### 8. 用户数据：隐私/历史/进度
```bash
curl -s -X PUT http://localhost:8000/user/privacy \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"privacy_settings": {"share_data": false, "collect_limit": "minimal"}}'
curl -s "http://localhost:8000/user/history?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/user/progress?data_type=task_progress&goal_id=$GID" -H "Authorization: Bearer $TOKEN"
```

## 说明
- 文档字段详见 `docs/API.md` 与各模块 README；`openapi.yaml` 可用于生成前端 SDK 雏形。
- 本地/CI 测试默认使用共享 `FakeRedis`；生产需配置 Upstash Redis 与 JWT 密钥。
