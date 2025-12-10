# 简历服务接口说明

本模块提供简历上传解析、评分、优化建议、管理与模板导出接口，采用 Serverless Redis 作为数据存储，认证复用用户模块的 JWT。

## 配置
- 配置文件：`resumes/config.py`
  - `RESUME_REDIS_REST_URL`、`RESUME_REDIS_REST_TOKEN`：专用简历库连接
  - `MAX_FILE_MB`：上传文件大小上限（默认 5MB）
  - `ALLOWED_EXPORT_TEMPLATES`：支持的模板集合（默认：`basic`、`modern`、`compact`）
- Redis 客户端：`resumes/redis_client.py`

## 路由与文件
- `resumes/urls.py`
  - `POST /resume/upload` → `resumes/api/upload.py:14`
  - `GET  /resume/score` → `resumes/api/score.py:8`
  - `GET  /resume/optimize` → `resumes/api/optimize.py:8`
- `POST /resume/manage`（action 路由） → `resumes/api/manage.py:8`
  - `POST /resume/export` → `resumes/api/export.py:8`

## 数据键约定
- `resume:id:<resume_id>` → Hash（`user_id`、`resume_name`、`file_url`、`parsed_content`、`parse_status`、`is_default`、`created_at`）
- `resume:list:<user_id>` → 逗号分隔的 `resume_id` 列表

## 接口定义

### 上传解析 `POST /resume/upload`
表单参数：`resume_name`、`resume_file`(multipart)、可选 `skills`（JSON 数组或逗号分隔）；用户身份从 JWT 的 `sub` 解析
响应：`resume_id`、`file_url`、`parsed_content`、`parse_status`
错误码：`2001` 格式不支持、`2002` 解析失败、`2003` 文件过大、`1008` 权限不足

示例：
```bash
curl -s -X POST http://localhost:8000/resume/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F resume_name="My Resume" \
  -F resume_file=@./resume.docx \
  -F skills='["Python","Django"]'
```

### 评分 `GET /resume/score`
参数：`resume_id`；用户身份从 JWT 的 `sub` 解析
响应：`overall_score`、`detail_scores`、`generated_date`
错误码：`2004` 简历不存在、`1008` 权限不足

示例：
```bash
curl -s "http://localhost:8000/resume/score?resume_id=$RID" \
  -H "Authorization: Bearer $TOKEN"
```

### 优化建议 `GET /resume/optimize`
参数：`resume_id`、可选 `target_job`；用户身份从 JWT 的 `sub` 解析
响应：`optimization_suggestions`（结构化列表）
错误码：`2004` 简历不存在、`1006` 权限不足

示例：
```bash
curl -s "http://localhost:8000/resume/optimize?resume_id=$RID&target_job=Backend" \
  -H "Authorization: Bearer $TOKEN"
```

### 管理 `POST /resume/manage`（action 路由）
- `action=list`：返回当前用户的简历列表（`resume_id|resume_name|is_default`）
- `action=get`：体含 `resume_id`，返回单条 `resume` 对象
- `action=update`：体含 `resume_id`，可选 `resume_name|is_default`
- `action=delete`：体含 `resume_id`
错误码：`2004` 简历不存在、`2005` 默认简历不可删除、`1008` 权限不足

示例：
```bash
# 列表（POST action=list）
curl -s -X POST http://localhost:8000/resume/manage \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"list"}'
# 设为默认（POST action=update）
curl -s -X POST http://localhost:8000/resume/manage \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"update","resume_id":"'$RID'","is_default":true}'
# 删除（POST action=delete）
curl -s -X POST http://localhost:8000/resume/manage \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"action":"delete","resume_id":"'$RID'"}'
```

### 模板导出 `POST /resume/export`
表单参数：`resume_id`、`template_id`(`basic|modern|compact`)、`export_format`(`PDF|DOCX`)；用户身份从 JWT 的 `sub` 解析
响应：`export_url`、`file_name`
错误码：`2006` 模板不存在、`2007` 导出失败（格式非法）

示例：
```bash
curl -s -X POST http://localhost:8000/resume/export \
  -H "Authorization: Bearer $TOKEN" \
  -F resume_id=$RID -F template_id=basic -F export_format=PDF
```

## 说明
- 当前上传仅存储文件元信息与简易解析结果，生产环境建议接入对象存储（如 Vercel Blob/S3）与解析服务（PDF/DOCX 解析）。
- 评分与建议为占位逻辑，便于端到端联调；后续可替换为真实模型或服务。
