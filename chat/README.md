# AI 助手对话模块

提供对话交互、简历完善引导与历史查询接口，统一使用 JWT 认证（身份从 `sub` 解析）。

## 配置
- `chat/config.py`：`CHAT_REDIS_REST_URL`、`CHAT_REDIS_REST_TOKEN`
- 客户端：`chat/redis_client.py`

## 路由与文件
- `chat/urls.py`
  - `POST /chat/interact` → `chat/api/interact.py:11`
  - `GET  /chat/resume_guide` → `chat/api/guide.py:6`
  - `GET  /chat/history` → `chat/api/history.py:6`
  - `GET  /chat/messages` → `chat/api/messages.py:6`（按会话分页获取消息）

## 错误码
- `5001` 对话服务异常（占位；当前实现正常返回）
- `2004` 简历不存在
- `5003` 无对话记录

## 键约定
- `chat:session:list:<user_id>` → 逗号分隔 `chat_id` 列表
- `chat:session:<chat_id>` → Hash（`user_id`、`chat_scene`、`created_at`、`last_ts`）
- `chat:messages:list:<chat_id>` → 逗号分隔 `message_id` 列表（按发生顺序）
- `chat:message:<message_id>` → Hash（`role:user|assistant` 与内容）

## 接口定义

### 对话交互 `POST /chat/interact`
参数：`message_content`、可选 `chat_scene`、可选 `chat_id`（续写会话）
响应：`reply_content`、`timestamp`、`chat_id`
示例：
```bash
curl -s -X POST http://localhost:8000/chat/interact \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"message_content":"请帮我看看简历","chat_scene":"resume"}'

# 续写同一会话
curl -s -X POST http://localhost:8000/chat/interact \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"message_content":"继续","chat_scene":"resume","chat_id":"<CHAT_ID>"}'
```

### 简历完善引导 `GET /chat/resume_guide`
参数：`resume_id`
响应：`guide_question`、`missing_field`
示例：
```bash
curl -s "http://localhost:8000/chat/resume_guide?resume_id=$RID" -H "Authorization: Bearer $TOKEN"
```

### 对话历史 `GET /chat/history`
参数：分页 `page`、`page_size`
响应：`chats` 列表（含 `chat_id`、`message_content`、`reply_content`、`timestamp`）与 `meta`
示例：
```bash
curl -s "http://localhost:8000/chat/history?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
```

## 说明
- 当前回复逻辑为规则占位；生产应替换为真实对话服务并接入观测与限流。
- 中间件会在响应头注入 `X-Request-ID`；错误响应统一为 `{ code, error }`。
### 会话消息 `GET /chat/messages`
参数：`chat_id`，分页 `page`、`page_size`
响应：`messages` 列表（`message_id`、`role`、`message_content|reply_content`、`timestamp`）与 `meta`
示例：
```bash
curl -s "http://localhost:8000/chat/messages?chat_id=<CHAT_ID>&page=1&page_size=20" -H "Authorization: Bearer $TOKEN"
```
