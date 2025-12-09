from core import redis_client


class PlansRepo:
    @staticmethod
    def client():
        return redis_client

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
        return redis_client.hgetall(PlansRepo.goal_id_key(goal_id)) if redis_client else {}

    @staticmethod
    def list_goals_by_user(user_id):
        cur = redis_client.get(PlansRepo.goal_list_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.hgetall(PlansRepo.goal_id_key(g)) for g in ids]

    @staticmethod
    def add_goal_to_user(user_id, goal_id):
        cur = redis_client.get(PlansRepo.goal_list_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if goal_id not in ids:
            ids.append(goal_id)
        redis_client.set(PlansRepo.goal_list_key(user_id), ",".join(ids))

    @staticmethod
    def remove_goal_from_user(user_id, goal_id):
        cur = redis_client.redis.get(PlansRepo.goal_list_key(user_id)) or ""
        ids = [x for x in cur.split(",") if x and x != goal_id]
        redis_client.set(PlansRepo.goal_list_key(user_id), ",".join(ids))

    @staticmethod
    def update_goal(goal_id, mapping):
        redis_client.hset(PlansRepo.goal_id_key(goal_id), mapping=mapping)

    @staticmethod
    def create_goal(goal_id, mapping):
        redis_client.hset(PlansRepo.goal_id_key(goal_id), mapping=mapping)

    @staticmethod
    def get_task(task_id):
        return redis_client.hgetall(PlansRepo.task_id_key(task_id)) if redis_client else {}

    @staticmethod
    def list_tasks_by_goal(goal_id):
        cur = redis_client.get(PlansRepo.task_list_key(goal_id)) or ""
        ids = [x for x in cur.split(",") if x]
        return [redis_client.hgetall(PlansRepo.task_id_key(t)) for t in ids]

    @staticmethod
    def add_task_to_goal(goal_id, task_id):
        cur = redis_client.get(PlansRepo.task_list_key(goal_id)) or ""
        ids = [x for x in cur.split(",") if x]
        if task_id not in ids:
            ids.append(task_id)
        redis_client.set(PlansRepo.task_list_key(goal_id), ",".join(ids))

    @staticmethod
    def update_task(task_id, mapping):
        redis_client.hset(PlansRepo.task_id_key(task_id), mapping=mapping)

    @staticmethod
    def create_task(task_id, mapping):
        redis_client.hset(PlansRepo.task_id_key(task_id), mapping=mapping)
