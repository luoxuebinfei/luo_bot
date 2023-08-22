# luo_Bot

<font size=4>基于 NoneBOt2 和 go-cqhttp 的机器人</font>

<font size=5>**⚠ 本项目使用了大量的浏览器服务，因此需要一定的机器性能运行，低配置机器使用时可能出现一些错误或其他问题！！**</font>

# 项目使用的插件
- [nonebot_plugin_gocqhttp](https://github.com/mnixry/nonebot-plugin-gocqhttp)
- [nonebot_plugin_apscheduler](https://github.com/nonebot/plugin-apscheduler)
- [nonebot-plugin-reboot](https://github.com/18870/nonebot-plugin-reboot)

## 二次修改的插件
- [ELF_RSS](https://github.com/Quan666/ELF_RSS)
- [YetAnotherPicSearch](https://github.com/NekoAria/YetAnotherPicSearch)

# 已实现功能
1. 优惠推送

    - 5分钟内相似度过高的文本不推送
    - 自动清理超过5分钟的推送

2. 搜图

    目前支持的搜图服务：

    - [Ascii2D](https://ascii2d.net/)
    - [Baidu](https://graph.baidu.com/)
    - [E-Hentai](https://e-hentai.org/)
    - [ExHentai](https://exhentai.org/)
    - [Google](https://www.google.com/imghp)
    - [Iqdb](https://iqdb.org/)
    - [SauceNAO](https://saucenao.com/)
    - [TraceMoe](https://trace.moe/)
    - [Yandex](https://yandex.com/images/search)
    - [SoutuBot](https://soutubot.moe/)

3. RSS 订阅
   - B站和推特动态的截图发送

# 开始使用

## Windows

默认已安装 `Python 3.11` 、 `pipenv` 和 `webview2`

1. 下载源码
```git clone https://github.com/luoxuebinfei/luo_bot.git```

2. 进入源码目录打开 `cmd`

   创建虚拟环境

   ```pipenv shell```

   安装依赖

   ```pipenv install```

   进入虚拟环境中安装 `nb-cli`

   ```pipenv install nb-cli```

   安装 nb 插件(根据 `pyproject.toml` 文件中的插件列表进行安装)

    ```
   nb plugin install nonebot-plugin-apscheduler
   nb plugin install nonebot-plugin-gocqhttp
   nb plugin install nonebot-plugin-reboot
   ```

3. 安装 `playwright` 无头浏览器

   ```playwright install firefox```

4. 下载 [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 解压运行

5. 运行

   ```python bot.py```

# 插件配置

编辑根目录下的 `.env.*` 文件，可根据实际使用需求修改相关配置

(如不存在，可以自行创建 `.env` -> `.env.dev` -> `.env.prod` 后面文件中相同的设置会覆盖前面文件的设置)

<details>
  <summary>示例</summary>

```
ENVIRONMENT=dev
DRIVER=~fastapi
HOST=127.0.0.1  # go-cqhttp监听地址
PORT=8080   # go-cqhttp监听端口

COMMAND_START=["/"]  # 配置命令起始字符
COMMAND_SEP=["."]  # 配置命令分割字符

# 插件 YetAnotherPicSearch 的配置
PROXY=""   # 代理地址
# saucenao APIKEY，必填，否则无法使用 saucenao 搜图
SAUCENAO_API_KEY=""
# 对 saucenao 的搜索结果进行 NSFW 判断的严格程度(依次递增), 启用后自动隐藏相应的 NSFW 结果的缩略图
# 0 表示不判断， 1 只判断明确的， 2 包括可疑的， 3 非明确为 SFW 的
SAUCENAO_NSFW_HIDE_LEVEL=1
# exhentai cookies，选填，没有的情况下自动改用 e-hentai 搜图
EXHENTAI_COOKIES=""
#NSFW_IMG=True   # 对可能出现的 nsfw 预览图片全部打码，默认为 False
#HIDE_IMG=False  # 隐藏所有搜索结果的缩略图，默认为 False
# 图片审核 API，到 https://moderatecontent.com/ 注册
REVIEW_KEY=""

# 插件 XianbaoPush 的配置
XIANBAO_OPEN=False  # 是否开启推送
XIANBAO_GROUP_ID=[] # 要推送的群,多个群以英文逗号分割

# 插件 ELF_RSS2 的配置
RSS_PROXY=""  # 代理地址 示例： "127.0.0.1:7890"
RSSHUB=""  # rsshub订阅地址
#RSSHUB_BACKUP=[]  # 备用rsshub地址 示例： ["https://rsshub.app","https://rsshub.app"] 务必使用双引号！！！
DB_CACHE_EXPIRE=30  # 去重数据库的记录清理限定天数
LIMIT=200  # 缓存rss条数
MAX_LENGTH=1024  # 正文长度限制，防止消息太长刷屏，以及消息过长发送失败的情况
ENABLE_BOOT_MESSAGE=false  # 是否启用启动时的提示消息推送

# 图片压缩
ZIP_SIZE=2048  # 非 GIF 图片压缩后的最大长宽值，单位 px
GIF_ZIP_SIZE=6144  # GIF 图片压缩临界值，单位 KB
IMG_FORMAT="{subs}/{name}{ext}" # 保存图片的文件名,可使用 {subs}:订阅名 {name}:文件名 {ext}:文件后缀(可省略)
IMG_DOWN_PATH=""  # 图片的下载路径,默认为./data/image 可以为相对路径(./test)或绝对路径(/home)

BLOCKQUOTE=true  # 是否显示转发的内容(主要是微博)，默认打开，如果关闭还有转发的信息的话，可以自行添加进屏蔽词(但是这整条消息就会没)
#BLACK_WORD=[]  # 屏蔽词填写 支持正则，如 ["互动抽奖","微博抽奖平台"] 务必使用双引号！！！

# 使用百度翻译API 可选，填的话两个都要填，不填默认使用谷歌翻译(需墙外？)
# 百度翻译接口appid和secretKey，前往http://api.fanyi.baidu.com/获取
# 一般来说申请标准版免费就够了，想要好一点可以认证上高级版，有月限额，rss用也足够了
#BAIDU_ID=""
#BAIDU_KEY=""

# qbittorrent 相关设置(文件下载位置等更多设置请在qbittorrent软件中设置)
#QB_USERNAME=""  # qbittorrent 用户名
#QB_PASSWORD=""  # qbittorrent 密码
#QB_WEB_URL="http://127.0.0.1:8081"  # qbittorrent 客户端默认是关闭状态，请打开并设置端口号为 8081，同时勾选 “对本地主机上的客户端跳过身份验证”
#QB_DOWN_PATH=""  # qb的文件下载地址，这个地址必须是 go-cqhttp能访问到的
#DOWN_STATUS_MSG_GROUP=[]  # 下载进度消息提示群组 示例 [12345678] 注意：最好是将该群设置为免打扰
#DOWN_STATUS_MSG_DATE=10  # 下载进度检查及提示间隔时间，秒，不建议小于 10s

# pikpak 相关设置
#PIKPAK_USERNAME=""  # pikpak 用户名
#PIKPAK_PASSWORD=""  # pikpak 密码
#PIKPAK_DOWNLOAD_PATH=""  # pikpak 离线保存的目录, 默认是根目录，示例: ELF_RSS/Downloads ,目录不存在会自动创建, 不能/结尾

```
</details>

# 指令

<details>
  <summary>RSS 订阅功能</summary>

> 注意：
>
> 1. 所有命令均分群组、子频道和私聊三种情况，执行结果也会不同
> 2. [] 包起来的参数表示可选，但某些情况下为必须参数
> 3. 所有订阅命令群管都可使用（但是有一定限制）
> 4. 私聊直接发送命令即可，群聊和子频道需在消息首部或尾部添加 **机器人昵称** 或者 **@机器人**
> 5. 群聊中也可以回复机器人发的消息执行命令，子频道暂不支持
> 6. 所有参数之间均用空格分割，符号为英文标点
> 7. 子频道中需要手动添加管理员频道号到 `GUILD_SUPERUSERS`

## 添加订阅

> 命令：add （添加订阅、sub）
>
> 参数：订阅名 [RSS 地址]
>
> 示例： `add test twitter/user/huagequan`
>
> 使用技巧：先快速添加订阅，之后再通过 `change` 命令修改
>
> 命令解释：
>
> 必需 `订阅名` 及 `RSS地址（RSSHub订阅源可以省略域名，其余需要完整的URL地址）` 两个参数，
> 订阅到当前 `群组` 、 `频道` 或 `QQ`。

## 添加 RSSHub 订阅

> 命令：rsshub_add
>
> 参数：[RSSHub 路由名] [订阅名]
>
> 示例： `rsshub_add github`
>
> 命令解释：
>
> 发送命令后，按照提示依次输入 RSSHub 路由、订阅名和路由参数

## 删除订阅

> 命令：deldy （删除订阅、drop、unsub）
>
> 参数：订阅名 [订阅名 ...]（支持批量操作）
>
> 示例： `deldy test` `deldy test1 test2`
>
> 命令解释：
>
> 1. 在超级管理员私聊使用该命令时，可完全删除订阅
> 2. 在群组使用该命令时，将该群组从订阅群组中删除
> 3. 在子频道使用该命令时，将该子频道从订阅子频道中删除

## 所有订阅

> 命令：show_all（showall，select_all，selectall，所有订阅）
>
> 参数：[关键词]（支持正则，过滤生效范围：订阅名、订阅地址、QQ 号、群号）
>
> 示例： `showall test` `showall 123`
>
> 命令解释：
>
> 1. 携带 `关键词` 参数时，展示该群组或子频道或所有订阅中含有关键词的订阅
> 2. 不携带 `关键词` 参数时，展示该群组或子频道或所有订阅
> 3. 当 `关键词` 参数为整数时候，只对超级管理员用户额外展示所有订阅中 `QQ号` 或 `群号` 含有关键词的订阅

## 查看订阅

> 命令：show（查看订阅）
>
> 参数：[订阅名]
>
> 示例： `show test`
>
> 命令解释：
>
> 1. 携带 `订阅名` 参数时，展示该订阅的详细信息
> 2. 不携带 `订阅名` 参数时，展示该群组或子频道或 QQ 的订阅详情

## 修改订阅

> 命令：change（修改订阅，moddy）
>
> 参数：订阅名[, 订阅名,...] 属性=值[ 属性=值 ...]
>
> 示例： `change test1[,test2,...] qq=,123,234 qun=-1`
>
> 使用技巧：可以先只发送 `change` ，机器人会返回提示信息，无需记住复杂的参数列表
>
> 对应参数:
>
> | 修改项             | 参数名       | 值范围                            | 备注                                                                                                                                               |
> |-----------------|-----------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
> | 订阅名             | -name     | 无空格字符串                         | 禁止将多个订阅批量改名，会因为名称相同起冲突                                                                                                                           |
> | 订阅链接            | -url      | 无空格字符串                         | RSSHub 订阅源可以省略域名，其余需要完整的 URL 地址                                                                                                                  |
> | QQ 号            | -qq       | 正整数 / -1                       | 需要先加该对象好友；前加英文逗号表示追加；-1 设为空                                                                                                                      |
> | QQ 群            | -qun      | 正整数 / -1                       | 需要先加入该群组；前加英文逗号表示追加；-1 设为空                                                                                                                       |
> | 更新频率            | -time     | 正整数 / crontab 字符串              | 值为整数时表示每 x 分钟进行一次检查更新，且必须大于等于 1<br />值为 crontab 字符串时，详见表格下方的补充说明                                                                                 |
> | 代理              | -proxy    | 1 / 0                          | 是否启用代理                                                                                                                                           |
> | 翻译              | -tl       | 1 / 0                          | 是否翻译正文内容                                                                                                                                         |
> | 仅标题             | -ot       | 1 / 0                          | 是否仅发送标题                                                                                                                                          |
> | 仅图片             | -op       | 1 / 0                          | 是否仅发送图片 (正文中只保留图片)                                                                                                                               |
> | 仅含有图片           | -ohp      | 1 / 0                          | 仅含有图片不同于仅图片，除了图片还会发送正文中的其他文本信息                                                                                                                   |
> | 下载种子            | -downopen | 1 / 0                          | 是否进行 BT 下载 (需要配置 qBittorrent，参考：[第一次部署](部署教程.md#第一次部署))                                                                                          |
> | 白名单关键词          | -wkey     | 无空格字符串 / 空                     | 支持正则表达式，匹配时推送消息及下载<br />设为空 (wkey=) 时不生效<br />前面加 +/- 表示追加/去除，详见表格下方的补充说明                                                                        |
> | 黑名单关键词          | -bkey     | 无空格字符串 / 空                     | 同白名单关键词，但匹配时不推送，可在避免冲突的情况下组合使用                                                                                                                   |
> | 种子上传到群          | -upgroup  | 1 / 0                          | 是否将 BT 下载完成的文件上传到群 (需要配置 qBittorrent，参考：[第一次部署](部署教程.md#第一次部署))                                                                                  |
> | 去重模式            | -mode     | link / title / image / or / -1 | 分为按链接 (link)、标题 (title)、图片 (image) 判断<br />其中 image 模式，出于性能考虑以及避免误伤情况发生，生效对象限定为只带 1 张图片的消息<br />此外，如果属性中带有 or 说明判断逻辑是任一匹配即去重，默认为全匹配<br />-1 设为禁用 |
> | 图片数量限制          | -img_num  | 正整数                            | 只发送限定数量的图片，防止刷屏                                                                                                                                  |
> | 正文待移除内容         | -rm_list  | 无空格字符串 / -1                    | 从正文中要移除的指定内容，支持正则表达式<br />因为参数解析的缘故，格式必须如：`rm_list='a'` 或 `rm_list='a','b'` <br />该处理过程是在解析 html 标签后进行的<br />要将该参数设为空，使用 `rm_list='-1'`          |
> | 停止更新            | -stop     | 1 / 0                          | 对订阅停止、恢复检查更新                                                                                                                                     |
> | PikPak 离线下载     | -pikpak   | 1 / 0                          | 将磁力链接离线到 PikPak 网盘，方便追番                                                                                                                          |
> | PikPak 离线下载路径匹配 | -ppk      | 无空格字符串                         | 匹配正文中的关键字作为目录                                                                                                                                    |
> | 发送合并消息          | -forward  | 1 / 0                          | 当一次更新多条消息时，尝试发送合并消息                                                                                                                              |
> 
> **注：**
>
> 各个属性之间使用**空格**分割
>
> wkey / bkey 前面加 +/- 表示追加/去除，最终处理为格式如 `a` 、 `a|b` 、 `a|b|c` …… 
>
> 如要使用，请在修改后检查处理后的正则表达式是否正确
>
> time 属性兼容 Linux crontab 格式，**但不同的是，crontab 中的空格应该替换为 `_` 即下划线**
>
> 可以参考 [Linux crontab 命令](https://www.runoob.com/linux/linux-comm-crontab.html) 务必理解！但实际有少许不同，主要是设置第 5 个字段时，即每周有不同。
>
> 时间格式如下：
>
> ```text
> f1_f2_f3_f4_f5
> ```
>
> - 其中 f1 是表示分钟，f2 表示小时，f3 表示一个月份中的第几日，f4 表示月份，f5 表示一个星期中的第几天。program 表示要执行的程序。
> - 当 f1 为 *时表示每分钟都要执行 program，f2 为* 时表示每小时都要执行程序，其馀类推
> - 当 f1 为 a-b 时表示从第 a 分钟到第 b 分钟这段时间内要执行，f2 为 a-b 时表示从第 a 到第 b 小时都要执行，其馀类推
> - 当 f1 为 */n 时表示每 n 分钟个时间间隔执行一次，f2 为*/n 表示每 n 小时个时间间隔执行一次，其馀类推
> - 当 f1 为 a, b, c, ... 时表示第 a, b, c, ... 分钟要执行，f2 为 a, b, c, ... 时表示第 a, b, c... 个小时要执行，其馀类推
>
> ```text
> *    *    *    *    *
> -    -    -    -    -
> |    |    |    |    |
> |    |    |    |    +----- 星期中星期几 (0 - 6) (星期一为 0，星期天为 6) (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
> |    |    |    +---------- 月份 (1 - 12)
> |    |    +--------------- 一个月中的第几天 (1 - 31)
> |    +-------------------- 小时 (0 - 23)
> +------------------------- 分钟 (0 - 59)
> ```
>
> 以下是一些示例：
>
> ``` text
> 1            # 每分钟执行一次（普通）
> 1_           # 每小时的第一分钟运行（cron）
> */1          # 每分钟执行一次
> *_*/1        # 每小时执行一次（注意，均在整点运行）
> *_*_*_*_0, 1, 2, 6 # 每周 1、2、3、日运行，周日为 6
> 0_6-12/3_*_12_* #在 12 月内, 每天的早上 6 点到 12 点，每隔 3 个小时 0 分钟执行一次
> *_12_*          # 每天 12 点运行
> # 如果不生效请查看控制台输出
> ```
</details>

<details>
  <summary>搜图</summary>

## 日常使用

- `搜图关键词` (`search_keyword`) 可以自定义，默认为 `搜图` ；之所以叫做关键词而不是指令，是因为它可以不在消息开头
- 如果想让机器人只响应含有 `搜图关键词` 的消息 (优先级高于 `search_immediately`) ，启用 `search_keyword_only`
- 私聊：
    - 发送 `搜图关键词` 及参数进入搜图模式，详见下方的 [搜图模式](#搜图模式)
    - 直接发送图片 (如果禁用了 `search_immediately` ，需要先发送 `搜图关键词` 进入搜图模式)
    - 回复自己或机器人发送的图片，在消息中附上 `搜图关键词` 及参数 (如果回复的是机器人，必须带上 `搜图关键词` 才会搜图，否则会被无视)
    - 回复**其他人**发送的图片时，需要将消息中的 `@昵称` 删除，再附上 `搜图关键词` 及参数
- 群聊：
    - 发送 `搜图关键词` 及参数进入搜图模式，详见下方的 `搜图模式`
    - `@机器人` 并发送图片
    - 回复某人 (包括自己) 发送的图片，在消息中附上 `搜图关键词` 或 `@机器人` 及参数 (如果回复的是机器人，必须带上 `搜图关键词` 才会搜图，否则会被无视)
- 可以在同一条消息中包含多张图片，会自动批量搜索
- 搜索图片时可以在消息内包含以下参数来指定搜索范围或者使用某项功能，优先级 (除去 `--purge`) 从上到下：
    - `--all` 全库搜索 (默认)
    - `--soutubot` 从 soutubot 中搜索
    - `--pixiv` 从 Pixiv 中搜索
    - `--danbooru` 从 Danbooru 中搜索
    - `--doujin` 搜索本子
    - `--anime` 搜索番剧
    - `--a2d` 使用 Ascii2D 进行搜索 (优势搜索局部图能力较强)
    - `--baidu` 使用 Baidu 进行搜索
    - `--ex` 使用 ExHentai (E-Hentai) 进行搜索
    - `--google` 使用 Google 进行搜索
    - `--iqdb` 使用 Iqdb 进行搜索
    - `--yandex` 使用 Yandex 进行搜索
    - `--purge` 无视缓存进行搜图，并更新缓存
- 对于 SauceNAO：
    - 如果得到的结果相似度低于 60% (可配置)，会自动使用 Ascii2D 进行搜索 (可配置)
    - 如果额度耗尽，会自动使用 Ascii2D 进行搜索
    - 如果搜索到本子，会自动在 ExHentai (E-Hentai) 中搜索并返回链接 (如果有汉化本会优先返回汉化本链接)
    - 如果搜到番剧，会自动使用 WhatAnime 搜索番剧详细信息：
        - AnimeDB 与 WhatAnime 的结果可能会不一致，是正常现象，毕竟这是两个不同的搜索引擎
        - 同时展示这两个搜索的目的是为了尽力得到你可能想要的识别结果
- 对于 ExHentai：
    - 如果没有配置 `EXHENTAI_COOKIES` ，会自动使用 `E-Hentai` 搜索 (如何获取 cookies 请参考 [PicImageSearch 文档](https://pic-image-search.kituin.fun/wiki/picimagesearch/E-hentai/DataStructure/#cookies%E8%8E%B7%E5%8F%96))
    - 不支持单色图片的搜索，例如黑白漫画，只推荐用于搜索 CG 、画集、图集、彩色漫画、彩色封面等
    - 如果没有配置 `superusers` ，不会显示搜索结果的收藏状态

## 搜图模式

搜图模式存在的意义是方便手机用户在转发图片等不方便在消息中夹带 @ 或搜图参数的情况下指定搜索范围或者使用某项功能：

- 发送 `搜图关键词` 并附上搜索范围或者功能参数，如果没有指定，会使用默认设置 (即 `--all`)
- 此时你发出来的下一条消息中的图 (也就是一次性的) 会使用指定搜索范围或者使用某项功能

</details>

# 其他需要开启的服务

- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) 用于解决 Cloudflare 的机器人验证，其默认端口 `8191` 不能更改
- [RSSHub](https://docs.rsshub.app/install/) 用于自建 RSS 订阅，如不需要则不用开启（`.env.*` 文件中 `RSSHUB` 一项）

# 一些文件生成

1. 用于伪装无头浏览器的`stealth.min.js`文件

   ```npx extract-stealth-evasions```

   也可以在 [stealth.min.js](https://gitcode.net/mirrors/requireCool/stealth.min.js?utm_source=csdn_github_accelerator)
   中进行下载

# 缓存文件所在位置

1. `playwright` 下载的浏览器位置

    `%USERPROFILE%\AppData\Local\ms-playwright` 在 Windows 上

    `~/Library/Caches/ms-playwright` 在 MacOS 上

    `~/.cache/ms-playwright` 在Linux上