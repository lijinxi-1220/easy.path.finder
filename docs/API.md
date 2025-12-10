# Easy Path Finder 接口参考（IDL）

- 认证：除注册/登录/发送验证码外，均需 `Authorization: Bearer <JWT>`。
- 错误：统一返回 `{ code: <int>, error: <string> }`。
- 分页：`page` 默认 1，`page_size` 默认 20；返回 `meta.total|page|page_size`。

## 用户
- POST `/register`
  - 请求体：`username|string`、`password|string`、`email|string?`、`phone_number|string?`
  - 响应：`user_id|string`、`username|string`、`registration_date|ISO8601`、`token|JWT`
- POST `/login`
  - 请求体：三选一 `username|string|email|string|phone_number|string` + `password|string`
  - 响应：`user_id|string`、`token|JWT`、`last_login_date|ISO8601`
- POST `/send_code`
  - 请求体：`email|string?` 或 `phone_number|string?`
  - 响应：`code|string`（测试环境返回）
- POST `/login/code`
  - 请求体：二选一标识 + `code|string`
  - 响应：同登录
- GET `/profile/{user_id}`
  - 路径：`user_id`
  - 响应：用户资料 Hash
- PUT `/profile/{user_id}`
  - 请求体：`full_name|string?`、`gender|string?`、`avatar_url|string?`
  - 响应：更新后的完整资料
- POST `/logout`
  - 响应：`success|bool`

## 简历
- POST `/resume/upload`（multipart）
  - 表单：`resume_name|string`、`resume_file|file`、`skills|json-array|string?`
  - 响应：`resume_id|string`、`file_url|string`、`parsed_content|json`、`parse_status|string`
- GET `/resume/score`
  - 参数：`resume_id|string`
  - 响应：`overall_score|int`、`detail_scores|object`、`generated_date|ISO8601`
- GET `/resume/optimize`
  - 参数：`resume_id|string`、`target_job|string?`
  - 响应：`optimization_suggestions|array`
- POST `/resume/manage`（action 路由）
  - `action=list`：响应 `resumes|array<{ resume_id, resume_name, is_default }>`
  - `action=get`：请求体：`resume_id|string`；响应 `resume|object`
  - `action=update`：请求体：`resume_id|string|resume_name|string?|is_default|bool?`；响应 `resume|object`
  - `action=delete`：请求体：`resume_id|string`；响应 `{ deleted: true }`
- POST `/resume/export`（multipart）
  - 表单：`resume_id|string`、`template_id|enum(basic|modern|compact)`、`export_format|enum(PDF|DOCX)`
  - 响应：`export_url|string`、`file_name|string`

## 匹配
- GET `/match/job_profile`
  - 参数：`job_title|string`、`industry|string?`
  - 响应：`job_profile_id|string|job_title|company|required_skills|array|required_experience|industry`
- POST `/match/analysis`
  - 请求体：`resume_id|string`、`target_type|enum(job|school)`、`target_id|string?`、`user_id|string?`（管理员代操作）
  - 响应：`match_id|string|match_percentage|int|match_details|object`
- GET `/match/recommend`
  - 参数：`preference|enum(job|school|both)`、`resume_id|string?`
  - 响应：`jobs|array<{ job_title, company, match_percentage }>`、`schools|array<{ school_name, major, rank }>`
- GET `/match/job_detail`
  - 参数：`job_profile_id|string`
  - 响应：岗位完整信息
- GET `/match/school_detail`
  - 参数：`school_id|string`
  - 响应：院校完整信息
- 管理导入（管理员）
  - POST `/match/admin/job_profiles/import`：数组项 `job_profile_id|job_title|company|required_skills|array|required_experience|industry`
  - POST `/match/admin/schools/import`：数组项 `school_id|school_name|major|rank|slug`

## 规划
- POST/PUT/DELETE/GET `/plan/goals`
  - GET 参数：`goal_id?` + 列表筛选 `status|q|due_from|due_to|sort_by|sort_order|page|page_size`
  - POST 统一入口（action 路由化）：
    - `action=list`：体内同 GET 列表参数；响应 `goals|meta`
    - `action=get`：`goal_id`；响应单目标
    - `action=create`：`goal_name|description|target_date`；响应创建目标
    - `action=update`：`goal_id` + 更新字段；响应更新目标
    - `action=delete`：`goal_id`；响应 `{ deleted: true }`
- POST `/plan/tasks/generate`
  - 请求体：`goal_id`
  - 响应：`tasks|array<{ task_id, task_name, due_date, priority, status }>`
- GET/POST/PUT `/plan/tasks`
  - GET 参数：`goal_id` + 列表筛选
  - POST 统一入口：
    - `action=list`：`goal_id` + 列表筛选；响应 `tasks|meta`
    - `action=generate`：`goal_id`；响应 `tasks`
    - 默认创建：`goal_id|task_name` + 可选 `due_date|priority|status`；响应单任务
  - PUT 请求体：`task_id` + 可选更新字段；响应更新任务
- GET `/plan/doc`
  - 参数：`goal_id?`
  - 响应：`plan_doc_url|string|plan_content|object`
- POST `/plan/adjust`
  - 请求体：`goal_id|string|task_completion|array<{ task_id, status }>`
  - 响应：`adjusted_goal|object|adjustment_reason|string|updated_at|ISO8601`

## 对话
- POST `/chat/interact`
  - 请求体：`message_content|string|chat_scene|string?|chat_id|string?`
  - 响应：`reply_content|string|timestamp|ISO8601|chat_id|string`
- GET `/chat/resume_guide`
  - 参数：`resume_id|string`
  - 响应：`guide_question|array|string|missing_field|array|string`
- GET `/chat/history`
  - 参数：`page|int|page_size|int`
  - 响应：`chats|array<{ chat_id, message_content, reply_content, timestamp }>|meta|object`
- GET `/chat/messages`
  - 参数：`chat_id|string|page|int|page_size|int`
  - 响应：`messages|array<{ message_id, role, message_content, reply_content, timestamp }>|meta|object`

## 增值服务
- GET `/service/recommend`
  - 参数：`service_type|enum(course|internship)|page|page_size|sort_by|sort_order`
  - 响应：`recommendations|array<{ name, intro, provider, link }>|meta|object`
- GET `/service/mentors`
  - 参数：`field|string|page|page_size|sort_by|sort_order`
  - 响应：`mentors|array<{ id, name, title, years, fee }>|meta|object`
- POST `/service/consult`
  - 请求体：`mentor_id|string|consult_topic|string?|consult_time|ISO8601?`
  - 响应：`application_id|user_id|mentor_id|consult_topic|consult_time|application_status|feedback`
- GET `/service/projects`
  - 参数：`project_type|string|page|page_size|sort_by|sort_order`
  - 响应：`projects|array<{ name, intro, time, location, method }>|meta|object`
- POST `/service/subscription`
  - 请求体：`subscription_type|enum(month|quarter|year)|payment_info|object`
  - 响应：`subscription_status|string|expire_date|ISO8601|privileges|array`
- POST `/service/subscription/webhook`
  - 头：`X-Signature|HMAC-SHA256`
  - 体：`user_id|string|status|enum(active|failed)`
  - 响应：`ok|bool`
