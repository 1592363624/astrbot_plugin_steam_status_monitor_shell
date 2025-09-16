# Steam 状态监控插件V2

本插件用于定时轮询 Steam Web API，监控指定玩家的在线/离线/游戏状态变更，并在状态变化时推送通知。支持多 SteamID 监控，自动记录游玩日志，支持群聊分组，数据持久化，支持丰富指令。

## 功能特性
- 支持定时轮询多个 SteamID 的状态，分群管理
- 支持分群通知，群聊可独立配置监控玩家
- 检测玩家上线、下线、开始/切换/退出游戏等状态变更，自动推送游戏启动/关闭提醒
- 成就变动自动推送提醒
- 已配置自定义轮询频率，长久不在线的玩家最多30分钟查询一次状态
- 状态变更时自动生成并推送通知文本
- 自动获取游戏中文名（优先），无则回退英文名
- 记录玩家游玩日志（支持断线重连、继续游玩等情况的合并）
- 支持通过指令动态增删 SteamID、调整配置参数
- 支持查询玩家详细信息、导出游玩记录
- 插件数据持久化，重启后状态不丢失
- 支持成就推送、图片渲染、超能力趣味功能

## 快速上手
1. 在AstrBot网页后台的配置中配置 Steam_Web_API_Key：https://steamcommunity.com/dev/apikey
2. 在AstrBot网页后台的配置中配置 SGDB_API_KEY（可选）：用于获取更丰富的游戏封面图，可在 https://www.steamgriddb.com/profile/preferences/api 
3. 在需要进行提醒的群聊输入指令：
   `/steam addid [Steam64位ID]`  （如：/steam addid 7656119xxxxxxxxxx）
4. 启动轮询：
   `/steam on`  启动本群 Steam 状态监控，后续状态变更会自动推送。

## 注意事项
- 获取速度与是否成功获取 Steam 数据取决于网络环境。建议通过加速或魔法手段来保证稳定的查询状态。

## 演示截图
![开始游戏示例](str.jpg)
![结束游戏示例](stop.jpg)
![成就推送示例](achievement.jpg)


## 指令列表
- `/steam on` 启动本群Steam状态监控
- `/steam off` 停止本群Steam状态监控
- `/steam list` 列出本群所有玩家当前状态
- `/steam alllist` 列出所有群聊分组及玩家状态
- `/steam config` 查看当前插件配置
- `/steam set [参数] [值]` 设置配置参数（如 `/steam set poll_interval_sec 30`）
- `/steam addid [SteamID]` 添加SteamID到本群监控列表
- `/steam delid [SteamID]` 从本群监控列表删除SteamID
- `/steam openbox [SteamID]` 查看指定SteamID的全部详细信息
- `/steam rs` 清除所有状态并初始化
- `/steam achievement_on` 开启本群Steam成就推送
- `/steam achievement_off` 关闭本群Steam成就推送
- `/steam test_achievement_render [steamid] [gameid] [数量]` 测试成就图片渲染
- `/.steam test_game_start_render [steamid] [gameid]` 测试开始游戏图片渲染
- `/steam清除缓存` 清除所有头像、封面图等图片缓存
- `/steam help` 显示所有指令帮助

## 运行说明
- 启动后，插件会自动定时轮询所有配置的 SteamID 状态。
- 检测到玩家上线、下线、开始/切换/退出游戏时，会自动推送通知。
- 插件支持断线重连、继续游玩等特殊情况的合并统计，游玩日志自动记录。
- 所有数据（游玩日志、状态等）自动持久化，重启后不丢失。

## 依赖
- Python 3.7+
- httpx
- Pillow
- AstrBot 框架

### 依赖安装方法
pip install httpx pillow

AstrBot版本： v3.5.13


