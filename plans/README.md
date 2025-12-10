# 职业路径规划接口说明

提供职业目标管理、阶段性任务生成与管理、规划书生成、动态调整接口。所有接口使用 JWT 认证，身份从 `sub` 解析。

## 接口定义与错误码

### 目标管理 `POST /plan/goals`：

- `action=list`：体内支持 `status|q|due_from|due_to|sort_by|sort_order|page|page_size`，响应 `goals` 与 `meta`
- `action=get`：`goal_id`，响应单目标对象
- `action=create`：`goal_name|description|target_date`，响应创建后的目标
- `action=update`：`goal_id` 与更新字段，响应更新后的目标
- `action=delete`：`goal_id`，响应 `{ deleted: true }`

示例：

```bash
# 新建目标
curl -s -X POST http://localhost:8000/plan/goals \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"goal_name":"Offer in 3 months","target_date":"2026-01-01"}'
```

{"goal_id": "858d12fa-de7c-4c5c-b2f2-0162c38ffce0", "user_id": "33672087-7aa3-436f-ae43-8b50555f8e79", "goal_name": "
Offer in 3 months", "description": "", "target_date": "2026-01-01", "status": "active", "created_at": "2025-12-10T07:57:
13.201948+00:00"


```bash
# 列表（POST）
curl -s -X POST http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"list","goal_id":"'$GID'","status":"pending","page":1,"page_size":10}'
# 生成（POST）
curl -s -X POST http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"generate","goal_id":"'$GID'"}'
# 创建（默认）
curl -s -X POST http://localhost:8000/plan/tasks \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"goal_id":"'$GID'","task_name":"完善技能清单"}'
```

### 规划书生成 `GET /plan/doc`

- 参数：可选 `goal_id`
- 响应：`plan_doc_url`、`plan_content`

### 路径动态调整 `POST /plan/adjust`

- 参数：`goal_id`、`task_completion`（任务完成状态列表）
- 响应：调整后的目标、`adjustment_reason`

## 待办事项
- 当前为占位实现，便于联调；生产可替换为规则/模型驱动的任务拆解与路径调整。
- doc/adjust接口暂未测试
