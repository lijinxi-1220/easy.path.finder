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

## 配置
- Webhook 密钥：`services/config.py:SUBSCRIPTION_WEBHOOK_SECRET`
- Redis 客户端：复用 `core.redis_client`

## IDL（请求/响应）
- `GET /service/recommend`
  - 请求参数：`service_type`(`course|internship`)、分页 `page|page_size`、排序 `sort_by|sort_order`
  - 响应字段：`recommendations` 列表项含 `name|intro|provider|link`，`meta.total|page|page_size`
- `GET /service/mentors`
  - 请求参数：`field`、分页 `page|page_size`、排序 `sort_by|sort_order`
  - 响应字段：`mentors` 列表项含 `id|name|title|years|fee`，`meta.total|page|page_size`
- `POST /service/consult`
  - 请求体：`mentor_id`、可选 `consult_topic|consult_time`
  - 响应字段：咨询申请详情 `application_id|user_id|mentor_id|consult_topic|consult_time|application_status|feedback`
- `GET /service/projects`
  - 请求参数：`project_type`、分页与排序同上
  - 响应字段：`projects` 列表项含 `name|intro|time|location|method`，`meta.total|page|page_size`
- `POST /service/subscription`
  - 请求体：`subscription_type`(`month|quarter|year`)、`payment_info`(对象)
  - 响应字段：订阅详情 `subscription_status|expire_date|privileges`
- `POST /service/subscription/webhook`
  - 请求头：`X-Signature`（HMAC-SHA256，密钥 `services/config.py:SUBSCRIPTION_WEBHOOK_SECRET`）
  - 请求体：`user_id`、`status`(`active|failed`)
  - 响应字段：`ok`

## 错误码（与代码一致）
- `1014` no_match（无匹配推荐）
- `1012` mentor not found（导师不存在）
- `1013` no_projects（无项目数据）
- `1015` payment failed（支付失败/回调校验失败）
- `1007` credentials error（凭证错误/未认证）
- `1002` request error / invalid params（请求/参数错误）

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

# 订阅回调（示例用 Python 计算 HMAC 签名）
PAYLOAD='{"user_id":"'$USER'","status":"active"}'
SIG=$(python3 - <<'PY'
import hmac, hashlib, os, sys
secret='dev-webhook-secret'
body=os.environ.get('PAYLOAD','').encode('utf-8')
print(hmac.new(secret.encode(), body, hashlib.sha256).hexdigest())
PY
)
curl -s -X POST http://localhost:8000/service/subscription/webhook \
  -H 'Content-Type: application/json' -H "X-Signature: $SIG" \
  -d "$PAYLOAD"
```

## 统一参数与校验
- 列表接口统一支持：`page`、`page_size`、`sort_by`、`sort_order`；参数非法返回 `{ code: 1002, error: 'invalid_param' }`
- 体校验（POST/PUT）使用 `validate_body`：必填字段缺失或类型错误返回 `{ code: 1002, error: 'invalid_param|invalid_json' }`
