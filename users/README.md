# 用户服务接口说明

本目录提供基于 Vercel + Django + Upstash Redis 的用户服务接口。当前所有接口均为 JSON API，认证使用 Bearer JWT。

## 环境与配置
- 配置文件：`users/config.py`
  - `UPSTASH_REDIS_REST_URL`、`UPSTASH_REDIS_REST_TOKEN`：Upstash Redis REST 连接
  - `JWT_SECRET`：JWT 签名密钥（本地默认 `dev-secret`）
  - `JWT_EXP_SECONDS`：JWT 有效期秒数（默认 604800 = 7 天）
- 生产部署时可改为读取环境变量，但当前版本按你的要求仅使用本地文件配置。

## 路由与文件
- 路由定义：`users/urls.py`
- 端点实现：
  - 注册：`users/api/register.py:11` → `POST /register`
  - 登录（账号/邮箱/手机号）：`users/api/login.py:11` → `POST /login`
  - 发送验证码：`users/api/code.py:10` → `POST /send_code`
  - 验证码登录：`users/api/code.py:34` → `POST /login/code`
  - 个人资料：`users/api/profile.py:8` → `GET/POST/PUT /profile/<user_id>`
  - 退出登录：`users/api/logout.py:6` → `POST /logout`

## 通用约定
- 请求头：`Content-Type: application/json`
- 认证头：`Authorization: Bearer <jwt>`（除注册、登录、发送验证码外）
- 键约定（Redis）：
  - `user:username:<username>` → `user_id`
  - `user:email:<email>` → `user_id`
  - `user:phone:<phone>` → `user_id`
  - `user:id:<user_id>` → Hash（用户资料）
  - `otp:email:<email>` / `otp:phone:<phone>` → 6 位验证码（5 分钟）
  - `jwt:blacklist:<jti>` → 退出黑名单（TTL 至过期）

### 统一响应与中间件
- 成功响应统一为 `ok({...})`，错误由抛出 `BusinessError(code, message, status)` 交由异常中间件处理，返回 `{ code, error }`。
- 全局接入 `Request-Id`、访问日志与统一异常处理中间件，便于排障与审计。
- 写操作支持幂等：通过请求头 `Idempotency-Key: <uuid>` 保证重复提交不产生副作用（如注册）。

## 接口定义

### 注册 `POST /register`
请求体：
```json
{ "username": "alice", "password": "pass123", "email": "a@x.com", "phone_number": "123" }
```
响应：
```json
{ "user_id": "...", "username": "alice", "registration_date": "...", "token": "<jwt>" }
```
错误：`1001` 用户名已存在、`1002` 参数缺失/JSON 无效、`500` Redis 未配置

### 登录（账号/邮箱/手机号 + 密码）`POST /login`
请求体（三选一 + password）：
```json
{ "username": "alice", "password": "pass123" }
{ "email": "a@x.com", "password": "pass123" }
{ "phone_number": "123", "password": "pass123" }
```
响应：
```json
{ "user_id": "...", "token": "<jwt>", "last_login_date": "...", "subscription_status": "active" }
```
错误：`1003` 账号或密码错误、`1004` 账号未激活、`500` Redis 未配置

### 发送验证码 `POST /send_code`
请求体（二选一）：
```json
{ "email": "a@x.com" }
{ "phone_number": "123" }
```
响应：`{ "success": true }`（当前版本仅生成并存储验证码，不实际发送）
错误：`1002` 参数缺失、`1005` 用户不存在、`1020` 频率限制（60 秒）、`500` Redis 未配置

### 验证码登录 `POST /login/code`
请求体：
```json
{ "email": "a@x.com", "code": "123456" }
```
或
```json
{ "phone_number": "123", "code": "123456" }
```
响应：同密码登录
错误：`1012` 验证码错误、其它同登录

### 个人资料 `GET/POST/PUT /profile/<user_id>`
- 认证：`Authorization: Bearer <jwt>`（本人访问；若访问他人资料需 `role=admin`）
- GET 响应：完整资料 Hash（如 `username`、`email`、`phone_number`、`full_name`、`gender`、`avatar_url`、`registration_date` 等）
- 更新字段：`full_name`、`gender`、`avatar_url`
错误：`1010` token 无效、`1006` 权限不足、`1005` 用户不存在

### 退出登录 `POST /logout`
- 认证：`Authorization: Bearer <jwt>`
- 响应：`{ "success": true }`（将 `jti` 加入黑名单）
错误：`1010` token 无效、`1011` token 过期

## cURL 验证示例

### 注册 → 登录 → 获取/更新资料 → 退出
```bash
# 注册
curl -s -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123","email":"a@x.com","phone_number":"123"}'

# 登录（用户名）
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .token)
USER=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .user_id)

# 获取资料
curl -s http://localhost:8000/profile/$USER -H "Authorization: Bearer $TOKEN"

# 更新资料
curl -s -X PUT http://localhost:8000/profile/$USER \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"full_name":"Alice","gender":"F"}'

# 退出
curl -s -X POST http://localhost:8000/logout -H "Authorization: Bearer $TOKEN"
```

### 验证码登录
```bash
# 注册
curl -s -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"bob","password":"pass456","email":"b@x.com","phone_number":"555"}'

# 请求验证码（邮箱）
curl -s -X POST http://localhost:8000/send_code \
  -H 'Content-Type: application/json' \
  -d '{"email":"b@x.com"}'

# 注意：当前版本不会真实发送邮件/短信；验证码保存在 Redis 的 `otp:email:b@x.com` 键中，TTL=300。
# 在生产环境应接入邮箱/短信服务并移除读取行为。

# 假设已获取验证码为 123456（仅测试场景）
TOKEN=$(curl -s -X POST http://localhost:8000/login/code \
  -H 'Content-Type: application/json' \
  -d '{"email":"b@x.com","code":"123456"}' | jq -r .token)
```

## 返回字段说明
- `user_id`：用户唯一 ID
- `token`：JWT 令牌，`Authorization: Bearer <token>`
- `last_login_date`、`registration_date`：ISO8601 UTC 时间
- `subscription_status`：订阅状态，默认 `active`
- 资料字段：`username`、`email`、`phone_number`、`full_name`、`gender`、`avatar_url` 等

## 测试
- 单元测试：`users/tests.py`，覆盖密码登录、验证码登录、退出后拒绝访问
- 运行：`python3 manage.py test -v 2`

## 安全与限流
- 验证码发送节流：60 秒；验证码有效期：5 分钟
- 登出使用 JWT 黑名单（基于 `jti`）
- 生产建议：接入邮件/短信服务、增加更严格的速率限制与审计日志
