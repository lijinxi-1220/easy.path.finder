# 职业路径规划接口说明

提供职业目标管理、阶段性任务生成与管理、规划书生成、动态调整接口。所有接口使用 JWT 认证，身份从 `sub` 解析。

## 配置
- `plans/config.py`：`PLANS_REDIS_REST_URL`、`PLANS_REDIS_REST_TOKEN`
- 客户端：`plans/redis_client.py`

## 路由与文件
- `plans/urls.py`
  - `POST/PUT/DELETE/GET /plan/goals` → 目标管理（`plans/api/goals.py:11`）
  - `POST /plan/tasks/generate` → 生成阶段性任务（`plans/api/tasks.py:21`）
  - `GET/POST/PUT /plan/tasks` → 任务管理（`plans/api/tasks.py:59`）
  - `GET /plan/doc` → 规划书生成（`plans/api/plan_doc.py:6`）
  - `POST /plan/adjust` → 路径动态调整（`plans/api/adjust.py:9`）

## 键约定
- `plan:goal:id:<goal_id>` → Hash（`user_id`、`goal_name`、`description`、`target_date`、`status`、`created_at`）
- `plan:goal:list:<user_id>` → 逗号分隔 `goal_id` 列表
- `plan:task:id:<task_id>` → Hash（`goal_id`、`task_name`、`due_date`、`priority`、`status` 等）
- `plan:task:list:<goal_id>` → 逗号分隔 `task_id` 列表

## 接口定义与错误码

### 目标管理 `POST/PUT/DELETE/GET /plan/goals`
- POST/PUT 参数：`goal_name`、`description`、`target_date`（更新还需 `goal_id`）
- DELETE 参数：`goal_id`
- GET 参数：可选 `goal_id`；列表支持筛选/排序/分页：
  - `status`、`q`、`due_from`、`due_to`
  - `sort_by`(`created_at|target_date|goal_name|status`)、`sort_order`(`asc|desc`)
  - `page`、`page_size`
- 响应：目标完整数据或列表，列表含 `meta.total/page/page_size`
- 错误：`4001` 目标不存在

IDL（POST 统一入口，`action` 路由化）：
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
# 列表
curl -s http://localhost:8000/plan/goals -H "Authorization: Bearer $TOKEN"
```

### 阶段性任务生成 `POST /plan/tasks/generate`
- 参数：`goal_id`
- 响应：`tasks` 列表（`task_id`、`task_name`、`due_date`、`priority`、`status`）
- 错误：`4001` 目标不存在

### 任务管理 `GET/POST/PUT /plan/tasks`
- GET 参数：`goal_id` → 返回任务列表；支持筛选/排序/分页：
  - `status`、`priority`、`due_from`、`due_to`
  - `sort_by`(`due_date|priority|created_at|task_name|status`)、`sort_order`(`asc|desc`)
  - `page`、`page_size`
- POST 参数：`goal_id`、`task_name`、可选 `due_date`、`priority`、`status`
- PUT 参数：`task_id`、可选 `task_name`、`due_date`、`priority`、`status`
- 错误：`4001` 目标不存在、`4003` 任务不存在

IDL（POST 统一入口，`action` 路由化）：
- `action=list`：体内支持 `goal_id|status|priority|due_from|due_to|sort_by|sort_order|page|page_size`
- `action=generate`：`goal_id`，响应 `tasks` 列表
- 默认创建：`goal_id|task_name` + 可选字段，响应单任务对象

示例：
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
- 错误：`4004` 生成失败（当前占位逻辑总能生成）

### 路径动态调整 `POST /plan/adjust`
- 参数：`goal_id`、`task_completion`（任务完成状态列表）
- 响应：调整后的目标、`adjustment_reason`
- 错误：`4001` 目标不存在

## 说明
- 当前为占位实现，便于联调；生产可替换为规则/模型驱动的任务拆解与路径调整。
