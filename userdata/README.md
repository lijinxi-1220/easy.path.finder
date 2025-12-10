# 用户数据与进度管理

提供隐私设置、历史记录查询与进度可视化数据接口。统一使用 JWT 认证。

## 接口
- 隐私设置 `PUT /user/privacy`
  - 请求体：`privacy_settings`（对象）
  - 响应字段：`privacy_settings|status`
- 历史查询 `GET /user/history`
  - 请求参数：`time_range`（`startISO,endISO` 可选）
  - 响应字段：`history` 列表项含 `action_type|action_content|timestamp`
- 进度数据 `GET /user/progress`
  - 请求参数：`data_type`(`task_progress|ability_trend`)、可选 `goal_id`
  - 响应字段：
    - `task_progress` 返回 `{ total|completed|rate }`
    - `ability_trend` 返回数组，如 `[{ week: "W1", score: 65 }, ... ]`

## 示例
```bash
# 更新隐私
curl -s -X POST http://localhost:8000/user/privacy \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"privacy_settings": {"share_data": false, "collect_limit": "minimal"}}'
# 历史查询
curl -s "http://localhost:8000/user/history?time_range=2025-01-01T00:00:00Z,2025-12-31T23:59:59Z" -H "Authorization: Bearer $TOKEN"
# 进度
curl -s "http://localhost:8000/user/progress?data_type=task_progress&goal_id=<GOAL_ID>" -H "Authorization: Bearer $TOKEN"
```
