# 岗位与院校匹配服务接口说明

基于 Serverless Redis 的岗位画像、匹配分析、推荐与详情查询模块。所有接口使用 JWT 认证，用户身份从 `Authorization: Bearer <jwt>` 的 `sub` 解析。

## 配置
- `matches/config.py`：`MATCH_REDIS_REST_URL`、`MATCH_REDIS_REST_TOKEN`
- 客户端：`matches/redis_client.py`

## 路由与文件
- `matches/urls.py`
  - `GET  /match/job_profile` → `matches/api/job_profile.py:5`
  - `GET  /match/job_detail` → `matches/api/job_profile.py:18`
  - `GET  /match/school_detail` → `matches/api/school_detail.py:5`
  - `POST /match/analysis` → `matches/api/match_analysis.py:12`
  - `GET  /match/recommend` → `matches/api/recommend.py:8`

## 键约定
- `job:profile:index:<job_title>:<industry>` → `job_profile_id`
- `job:profile:<job_profile_id>` → Hash（`job_title`、`company`、`required_skills`、`required_experience` 等）
- `school:index:<slug>` → `school_id`
- `school:id:<school_id>` → Hash（`school_name`、`major`、`rank` 等）
- `match:id:<match_id>` → 匹配结果存档

## 接口定义

### 岗位画像查询 `GET /match/job_profile`
参数：`job_title`，可选 `industry`
响应：`job_profile_id`、`required_skills`、`required_experience` 等画像数据
错误：`3001` 岗位画像不存在

示例：
```bash
curl -s "http://localhost:8000/match/job_profile?job_title=Software%20Engineer" \
  -H "Authorization: Bearer $TOKEN"
```

### 匹配度分析 `POST /match/analysis`
请求体：`resume_id`、`target_type`(`job|school`)、可选 `target_id`
响应：`match_id`、`match_percentage`、`match_details`
错误：`3002` 用户信息不完整，`3003` 目标不存在

示例：
```bash
curl -s -X POST http://localhost:8000/match/analysis \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"resume_id":"'$RID'","target_type":"job","target_id":"job-1"}'
```

### 双路径推荐 `GET /match/recommend`
参数：`preference`(`job|school|both`)、可选 `resume_id`
响应：岗位推荐列表（`job_title`、`company`、`match_percentage`）、院校推荐列表（`school_name`、`major`、`rank`）
错误：`3002` 用户信息不完整

示例：
```bash
curl -s "http://localhost:8000/match/recommend?preference=both" \
  -H "Authorization: Bearer $TOKEN"
```

### 岗位详情 `GET /match/job_detail`
参数：`job_profile_id`
响应：岗位完整信息
错误：`3001` 岗位画像不存在

### 院校详情 `GET /match/school_detail`
参数：`school_id`
响应：院校完整信息
错误：`3004` 院校信息不存在

## 说明
- 当前画像与院校数据需预先写入 Redis（参见键约定），生产环境建议连接职业画像/院校库或检索服务。
- 匹配与推荐为占位实现，便于端到端联调；可替换为召回+排序的真实策略。
