import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

nonebot.load_builtin_plugins('echo')

if __name__ == "__mp_main__":
    nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    # nonebot.load_plugin("nonebot_plugin_gocqhttp")
    nonebot.load_plugin("nonebot_plugin_apscheduler")
    nonebot.load_plugin("nonebot_plugin_reboot")
    nonebot.run()