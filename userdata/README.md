# 用户数据与进度管理

提供隐私设置、历史记录查询与进度可视化数据接口。统一使用 JWT 认证。

## 路由与文件
- `userdata/urls.py`
  - `PUT /user/privacy` → `userdata/api/privacy.py:8`
  - `GET /user/history` → `userdata/api/history.py:6`
  - `GET /user/progress` → `userdata/api/progress.py:6`

## 键约定
- `user:privacy:<user_id>` → Hash（`privacy_settings`、`status`）
- `user:history:list:<user_id>`、`user:history:id:<history_id>` → 历史记录

## 接口
- 隐私设置 `PUT /user/privacy`
  - 请求体：`privacy_settings`（对象）
  - 响应字段：`privacy_settings|status`
  - 错误：`1003` user not found（用户不存在）
- 历史查询 `GET /user/history`
  - 请求参数：`time_range`（`startISO,endISO` 可选）
  - 响应字段：`history` 列表项含 `action_type|action_content|timestamp`
  - 错误：`1009` user not found or no history（用户不存在或无历史）
- 进度数据 `GET /user/progress`
  - 请求参数：`data_type`(`task_progress|ability_trend`)、可选 `goal_id`
  - 响应字段：
    - `task_progress` 返回 `{ total|completed|rate }`
    - `ability_trend` 返回数组，如 `[{ week: "W1", score: 65 }, ... ]`
  - 错误：`1010` no planned data（无规划数据）、`1011` unsupported data type（数据类型不支持）

## 示例
```bash
# 更新隐私
curl -s -X PUT http://localhost:8000/user/privacy \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"privacy_settings": {"share_data": false, "collect_limit": "minimal"}}'
# 历史查询
curl -s "http://localhost:8000/user/history?time_range=2025-01-01T00:00:00Z,2025-12-31T23:59:59Z" -H "Authorization: Bearer $TOKEN"
# 进度
curl -s "http://localhost:8000/user/progress?data_type=task_progress&goal_id=<GOAL_ID>" -H "Authorization: Bearer $TOKEN"
```
