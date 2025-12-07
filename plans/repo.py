from . import redis_client


class PlansRepo:
    @staticmethod
    def goal_id_key(goal_id):
        return f"plan:goal:id:{goal_id}"

    @staticmethod
    def goal_list_key(user_id):
        return f"plan:goal:list:{user_id}"

    @staticmethod
    def task_id_key(task_id):
        return f"plan:task:id:{task_id}"

    @staticmethod
    def task_list_key(goal_id):
        return f"plan:task:list:{goal_id}"

    @staticmethod
    def get_goal(goal_id):
        return redis_client.redis.hgetall(PlansRepo.goal_id_key(goal_id)) if redis_client.redis else {}

    @staticmethod
    def list_goals_by_user(user_id):
        cur = redis_client.redis.get(PlansRepo.goal_list_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.redis.hgetall(PlansRepo.goal_id_key(g)) for g in ids]

    @staticmethod
    def add_goal_to_user(user_id, goal_id):
        cur = redis_client.redis.get(PlansRepo.goal_list_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if goal_id not in ids:
            ids.append(goal_id)
        redis_client.redis.set(PlansRepo.goal_list_key(user_id), ",".join(ids))

    @staticmethod
    def update_goal(goal_id, mapping):
        redis_client.redis.hset(PlansRepo.goal_id_key(goal_id), mapping=mapping)

    @staticmethod
    def get_task(task_id):
        return redis_client.redis.hgetall(PlansRepo.task_id_key(task_id)) if redis_client.redis else {}

    @staticmethod
    def list_tasks_by_goal(goal_id):
        cur = redis_client.redis.get(PlansRepo.task_list_key(goal_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.redis.hgetall(PlansRepo.task_id_key(t)) for t in ids]

    @staticmethod
    def add_task_to_goal(goal_id, task_id):
        cur = redis_client.redis.get(PlansRepo.task_list_key(goal_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if task_id not in ids:
            ids.append(task_id)
        redis_client.redis.set(PlansRepo.task_list_key(goal_id), ",".join(ids))

    @staticmethod
    def update_task(task_id, mapping):
        redis_client.redis.hset(PlansRepo.task_id_key(task_id), mapping=mapping)

