# 用户服务接口说明

当前所有接口均为 JSON API，认证使用 Bearer JWT。

## 通用约定

- 请求头：`Content-Type: application/json`
- 认证头：`Authorization: Bearer <jwt>`（除注册、登录、发送验证码外）

## 接口定义

### 注册 `POST /register`

请求体：

```json
{
  "username": "alice",
  "password": "pass123",
  "email": "a@x.com",
  "phone_number": "123"
}
```

响应：

```json
{
  "user_id": "...",
  "username": "alice",
  "registration_date": "...",
  "token": "<jwt>"
}
```

### 登录（账号/邮箱/手机号 + 密码）`POST /login`

请求体（三选一 + password）：

```json
{
  "username": "alice",
  "password": "pass123"
}
{
  "email": "a@x.com",
  "password": "pass123"
}
{
  "phone_number": "123",
  "password": "pass123"
}
```

响应：

```json
{
  "user_id": "...",
  "token": "<jwt>",
  "last_login_date": "..."
}
```

错误：`{ code, error }`（如凭证错误、频率限制等）

### 发送验证码 `POST /send_code`

请求体（二选一）：

```json
{
  "email": "a@x.com"
}
{
  "phone_number": "123"
}
```

响应：`{ "code": "123456" }`（测试环境返回；生产应通过邮件/短信发送）
错误：`1002` 参数缺失、`1003` 用户不存在、`1004` 频率限制（60 秒）、`500` Redis 未配置

### 验证码登录 `POST /login/code`

请求体：

```json
{
  "email": "a@x.com",
  "code": "123456"
}
```

或

```json
{
  "phone_number": "123",
  "code": "123456"
}
```

响应：同密码登录

### 个人资料 `POST /profile/<user_id>`

- 认证：`Authorization: Bearer <jwt>`（本人访问；若访问他人资料需 `role=admin`）
- 响应：完整资料 Hash（如 `username`、`email`、`phone_number`、`full_name`、`gender`、`avatar_url`、`registration_date` 等）
- 更新字段：`full_name`、`gender`、`avatar_url`

### 退出登录 `POST /logout`

- 认证：`Authorization: Bearer <jwt>`
- 响应：`{ "success": true }`（将 `jti` 加入黑名单）

## cURL 验证示例

### 注册 → 登录 → 获取/更新资料 → 退出

```bash
# 注册
curl -s -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice3","password":"pass123","email":"a@x.com","phone_number":"123"}'

{"user_id": "33672087-7aa3-436f-ae43-8b50555f8e79", "username": "alice3", "registration_date": "2025-12-10T06:31:48.285080+00:00", "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMzY3MjA4Ny03YWEzLTQzNmYtYWU0My04YjUwNTU1ZjhlNzkiLCJ1c2VyX2lkIjoiMzM2NzIwODctN2FhMy00MzZmLWFlNDMtOGI1MDU1NWY4ZTc5IiwidXNlcm5hbWUiOiJhbGljZTMiLCJyb2xlIjoidXNlciIsImp0aSI6IlNHcHpTZ0kwMnBFbzBGbzJSb1BNV0EiLCJleHAiOjE3NjU5NTMxMTAsImlhdCI6MTc2NTM0ODMxMH0.GZ1tWseGL9ifnU_IIQCrgYyy-XcWcLuWPLB_4wZd7u0"}

# 登录（用户名）
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .token)
USER=$(curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass123"}' | jq -r .user_id)

# 获取资料
curl -s http://localhost:8000/profile/$USER -H "Authorization: Bearer $TOKEN"

curl -s -X POST http://localhost:8000/profile/33672087-7aa3-436f-ae43-8b50555f8e79 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMzY3MjA4Ny03YWEzLTQzNmYtYWU0My04YjUwNTU1ZjhlNzkiLCJ1c2VyX2lkIjoiMzM2NzIwODctN2FhMy00MzZmLWFlNDMtOGI1MDU1NWY4ZTc5IiwidXNlcm5hbWUiOiJhbGljZTMiLCJyb2xlIjoidXNlciIsImp0aSI6IlNHcHpTZ0kwMnBFbzBGbzJSb1BNV0EiLCJleHAiOjE3NjU5NTMxMTAsImlhdCI6MTc2NTM0ODMxMH0.GZ1tWseGL9ifnU_IIQCrgYyy-XcWcLuWPLB_4wZd7u0"
 
# 更新资料
curl -s -X POST http://localhost:8000/profile/$USER \
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
- 资料字段：`username`、`email`、`phone_number`、`full_name`、`gender`、`avatar_url` 等


## 待办
- 暂未接入短信验证码