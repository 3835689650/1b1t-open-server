# 1b1t-open-server

Minecraft 一键开服 CLI 工具。

## 安装

```bash
curl -fsSL https://www.1b1t.cn/1b1t-apt-key.gpg | sudo tee /etc/apt/keyrings/1b1t.gpg >/dev/null
echo 'deb [signed-by=/etc/apt/keyrings/1b1t.gpg] https://www.1b1t.cn/1b1t-apt/ stable main' | sudo tee /etc/apt/sources.list.d/1b1t.list
sudo apt update && sudo apt install 1b1t-open-server
```

安装后命令: `1b1t`(同 `1b1t-open-server`)

## 用法

```bash
1b1t                        # 一键开服, 进入向导
1b1t start <目录>            # 按已有配置开服
1b1t stop|restart|status|doctor <目录>
1b1t console <目录> "say 你好"   # 向服务器控制台发命令
```

向导流程: ①选择版本(支持所有 MC 版本) ②选择目录 ③选择端口
④常见配置(正版验证/命令方块/死亡不掉落/MOTD/难度/人数/视距/白名单/PVP/种子/内存)
⑤高级选项(编辑 server.properties 全部项) → 自动下载核心并开服。

功能:
- 自动下载官方服务端 (BMCLAPI 镜像 + SHA1 校验)
- 自动匹配 Java (≤1.16.5→8, 1.17→16, 1.18-1.20.4→17, ≥1.20.5→21)
- 死亡不掉落等游戏规则开服后自动注入
- doctor 自主排查: Java/端口/jar/EULA/磁盘/权限/内存/日志 8 项
- --dry-run 只生成配置

## 发布新版本

```bash
./build-apt.sh 1.0.1
```
