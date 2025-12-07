from .base import ChatProvider


class MockProvider(ChatProvider):
    def generate_reply(self, messages, scene):
        last = messages[-1]["content"] if messages else ""
        reply = "您好，我是职业助手。"
        if "简历" in last:
            reply = "我可以帮您完善简历与匹配岗位，是否需要引导问题？"
        elif "岗位" in last or "工作" in last:
            reply = "我们可以根据您的技能推荐岗位，您目前的目标行业是什么？"
        return reply

