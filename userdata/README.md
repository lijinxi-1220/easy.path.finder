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
  - 请求：`privacy_settings`（JSON）
  - 响应：当前设置与状态
  - 错误：`1005` 用户不存在
- 历史查询 `GET /user/history`
  - 参数：`time_range`（`startISO,endISO` 可选）
  - 响应：`history` 列表（操作类型、内容、时间）
  - 错误：`1005` 用户不存在或无历史
- 进度数据 `GET /user/progress`
  - 参数：`data_type`(`task_progress|ability_trend`)、可选 `goal_id`
  - 响应：图表数据；`task_progress` 返回 `total/completed/rate`
  - 错误：`4005` 无规划数据

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
