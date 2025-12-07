# 增值服务模块

提供课程/实习推荐、导师列表查询、导师咨询申请、国际项目推荐、会员订阅接口。统一使用 JWT 认证。

## 路由
- `services/urls.py`
  - `GET  /service/recommend` → 课程/实习推荐（`services/api/recommend.py:5`）
  - `GET  /service/mentors` → 导师列表查询（`services/api/mentors.py:5`）
  - `POST /service/consult` → 导师咨询申请（`services/api/consult.py:6`）
  - `GET  /service/projects` → 国际项目推荐（`services/api/projects.py:5`）
  - `POST /service/subscription` → 会员订阅（`services/api/subscription.py:6`）
  - `POST /service/subscription/webhook` → 会员订阅回调（`services/api/subscription_webhook.py:6`）

## 错误码
- `6001` 无匹配推荐
- `6002` 无导师
- `6003` 导师不存在
- `6004` 申请重复或参数错误
- `6005` 无项目数据
- `6006` 支付失败
- `6007` 订阅参数错误

## 示例
```bash
# 推荐
curl -s "http://localhost:8000/service/recommend?service_type=course&sort_by=name&sort_order=asc&page=1&page_size=20" -H "Authorization: Bearer $TOKEN"
# 导师
curl -s "http://localhost:8000/service/mentors?field=backend&sort_by=years&sort_order=desc&page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
# 咨询申请
curl -s -X POST http://localhost:8000/service/consult \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -H 'Idempotency-Key: req-123' \
  -d '{"mentor_id":"m1","consult_topic":"求职指导","consult_time":"2026-01-02T20:00:00Z"}'
# 项目
curl -s "http://localhost:8000/service/projects?project_type=exchange&sort_by=time" -H "Authorization: Bearer $TOKEN"
# 订阅
curl -s -X POST http://localhost:8000/service/subscription \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -H 'Idempotency-Key: req-456' \
  -d '{"subscription_type":"month","payment_info":{"channel":"mock"}}'
```

## 统一参数与校验
- 列表接口统一支持：`page`、`page_size`、`sort_by`、`sort_order`；参数非法返回 `{ code: 1002, error: 'invalid_param' }`
- 体校验（POST/PUT）使用 `validate_body`：必填字段缺失或类型错误返回 `{ code: 1002, error: 'invalid_param|invalid_json' }`
