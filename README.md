<div align="center">
  <h1 align="center">
    <img src="icons/icon.png" width="200" alt="ok-ef logo"/>
    <br/>
    ok-ef
  </h1> 

  <p>
    一个基于图像识别的终末地自动化程序，支持后台运行，基于 <a href="https://github.com/ok-oldking/ok-script">ok-script</a> 开发。
    <br />
    An image-recognition-based automation tool for End Field, with background mode support, developed with <a href="https://github.com/ok-oldking/ok-script">ok-script</a>.
  </p>

  <p><i>通过模拟 Windows 用户接口进行操作，无内存读取、无文件修改</i></p>
</div>

<!-- Badges -->
<div align="center">

![平台](https://img.shields.io/badge/platform-Windows-blue)
[![GitHub release](https://img.shields.io/github/v/release/ok-oldking/ok-end-field)](https://github.com/ok-oldking/ok-end-field/releases)
[![总下载量](https://img.shields.io/github/downloads/ok-oldking/ok-end-field/total)](https://github.com/ok-oldking/ok-end-field/releases)
[![Discord](https://img.shields.io/discord/296598043787132928?color=5865f2&label=%20Discord)](https://discord.gg/vVyCatEBgA)

</div>

### [English Readme](README_en.md) | 中文说明

**演示与教程:** [![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?style=for-the-badge&logo=YouTube&logoColor=white)](https://youtu.be/h6P1KWjdnB4)

---

## ⚠️ 免责声明

本软件为外部辅助工具，旨在自动化《终末地》的部分游戏流程。它完全通过模拟常规用户界面与游戏交互，遵循相关法律法规。本项目旨在简化用户的重复性操作，不会破坏游戏平衡或提供不公平优势，也绝不会修改任何游戏文件或数据。

本软件开源、免费，仅供个人学习与交流使用，请勿用于任何商业或营利性目的。开发者团队拥有本项目的最终解释权。因使用本软件而产生的任何问题，均与本项目及开发者无关。

请注意，根据鹰角官方的《终末地》公平运营声明：
> 严禁利用任何第三方工具破坏游戏体验。
> 我们将严厉打击使用外挂、加速器、作弊软件、宏脚本等违规工具的行为，这些行为包括但不限于自动挂机、技能加速、无敌模式、瞬移、修改游戏数据等操作。
> 一经查证，我们将视违规情况和次数，采取包括但不限于扣除违规收益、冻结或永久封禁游戏账号等措施。

**使用本软件即表示您已阅读、理解并同意以上声明，并自愿承担一切潜在风险。**

## 🚀 快速开始

1.  **下载安装包**：从下方的“下载渠道”中选择一个，下载最新的 `ok-ef-win32-China-setup.exe` 安装文件。
2.  **安装程序**：双击 `ok-ef-win32-China-setup.exe` 文件，并按照安装向导的提示完成安装。
3.  **运行程序**：安装完成后，从桌面快捷方式或开始菜单启动 `ok-ef` 即可。

## 📥 下载渠道

*   **[GitHub](https://github.com/ok-oldking/ok-end-field/releases)**: 官方发布页，全球访问速度快。（**请下载 `setup.exe` 安装包，而不是 `Source Code` 源码压缩包**）
*   **[Mirror酱](https://mirrorchyan.com/zh/projects?rid=ok-end-field&source=ok-ef-readme)**: 国内镜像，下载可能需要购买其平台的 CD-KEY。
*   **[夸克网盘](https://pan.quark.cn/s/a1052cec4d13)**: 国内网盘，免费，但需要注册并使用其客户端下载。

## ✨ 主要功能
<img width="1200" height="2805" src="https://github.com/user-attachments/assets/505044a5-7e9a-449f-98a1-de7502b4a1d9" />
<img width="1200" height="2505" src="https://github.com/user-attachments/assets/543d375a-e8d3-4c09-a310-800b872f42fa" />

### 🥬 日常任务
一键执行日常流程，支持模块化开关与独立配置。

- 送礼（支持最大尝试次数）
- 据点兑换
- 转交运送委托
- 领取委托奖励
- 造装备
- 日常奖励领取
- 收信用
- 好友助力策略（可优先仅收培育室）

---

### 🚚 自动送货
针对武陵 7.31w 委托的自动接单与送货系统。

- 自动识别滑索路径并送达指定目标
- 支持仅接单 / 仅送货模式
- 可选滚动放大视角提升对齐成功率
- 内置分叉测试与完整循环测试
- 支持路径自定义
- 提供教程视频

---

### 🧾 运送委托接取
自动识别高价值调度任务并抢单。

- 谷地券 / 武陵券独立开关
- 支持最低与最高金额区间设置
- 同时识别券种与报酬金额
- 条件不满足自动刷新

---

### 📦 仓库物品转移
跨仓库自动转运指定物品。

- 从发货仓库取出指定物品
- 自动切换到收货仓库并一键存放
- 支持最小保留数量保护
- 下拉选择仓库与物品
- 依赖 OCR + 模板识别

---

### 🔍 毕业基质识别
自动遍历武器基质列表，识别毕业词条并执行锁定操作。

- 自动上锁毕业基质
- 可选取消非毕业基质锁定
- 基于 `weapon_data.csv` 数据匹配
- 支持网格遍历与翻页扫描

---

### 🛒 自动拾取
大世界自动拾取触发任务。

- 自动识别可交互目标并执行拾取
- 内置白名单机制（采集类、虫类、植物类等）
- 黑名单过滤避免误操作
- 支持后台运行

---

### ⚔ 自动战斗
进入战斗后自动执行技能循环直至战斗结束。

- 自定义技能释放顺序（如 `123`）
- 设置启动技能点数阈值
- 满技能自动循环释放
- 支持后台结束战斗通知
- 自动识别战斗状态

---

### 🔐 自动登录
自动检测未登录状态并执行登录流程。

- 周期性触发检测
- 自动完成登录
- 支持月卡领取场景

---

### ⏭ 自动跳过剧情
自动检测剧情界面并跳过。

- 自动识别“跳过”按钮
- 自动按 `ESC`
- 自动点击确认
- 循环检测直至退出剧情

---




## 🔧 疑难解答 (Troubleshooting)

如果遇到问题，请在提问前按以下步骤逐一排查：

1.  **安装路径**：请确保软件安装在**纯英文路径**下（例如 `D:\Games\ok-ef`），不要安装在 `C:\Program Files` 或包含中文字符的文件夹中。
2.  **杀毒软件**：将软件的安装目录添加到您的杀毒软件（包括 Windows Defender）的**信任区或白名单**中，以防文件被误删或拦截。
3.  **显示设置**：
    *   关闭所有显卡滤镜（如 NVIDIA Game Filter）和锐化功能，除非部分功能要求。
    *   使用游戏默认的亮度设置。
    *   关闭任何在游戏画面上显示信息的叠加层（如 MSI Afterburner、Fraps 等显示的帧率）。
4.  **自定义按键**：如果您修改了游戏内的默认按键，请务必在 `ok-ef` 的设置中进行同步配置。仅支持设置中列出的按键。
5.  **软件版本**：检查并确保您使用的是最新版本的 `ok-ef`。
6.  **游戏性能**：请确保游戏能稳定在 **60 FPS** 运行。如果帧率不稳定，请尝试降低游戏画质或分辨率。
7.  **游戏断线**：如频繁遇到与服务器断开连接的问题，可以尝试先手动打开游戏运行5分钟后再启动本工具，或在断线后直接重新登录，不要退出游戏。
8.  **寻求帮助**：如果以上步骤都无法解决您的问题，请通过社区渠道提交详细的错误报告。
9. **游戏/软件语言** 本软件目前部分功能仅支持简体中文，不支持其他语言。

---

## 💻 开发者专区

### 从源码运行 (Python)

本项目仅支持 Python 3.12 版本, 必须以管理员权限启动CMD, PyCharm, VSCode。

```bash
# 安装或更新依赖
pip install -r requirements.txt --upgrade

# 运行 Release 版本
python main.py

# 运行 Debug 版本
python main_debug.py
```

### 命令行参数

您可以通过命令行参数实现自动化启动。

```bash
# 示例：启动后自动执行第一个任务（一条龙），并在任务完成后退出程序
ok-ef.exe -t 1 -e
```

*   `-t` 或 `--task`: 启动后自动执行第 N 个任务。`1` 代表任务列表中的第一个。
*   `-e` 或 `--exit`: 任务执行完毕后自动退出程序。

## 💬 加入我们

*   **QQ 交流群**: `940581952` (入群答案: `老王同学OK`)
*   **QQ 频道**: [点击加入](https://pd.qq.com/s/djmm6l44y) (群满或获取最新资讯)
*   **开发者群**: `1079581542` ( **注意**: 此群仅面向有开发能力、拥有Github账号、希望参与贡献的开发者，入群前请确保您已能够从源码成功运行项目。)

本项目基于 [ok-script](https://github.com/ok-oldking/ok-script) 框架开发，简单易维护。欢迎有兴趣的开发者使用 [ok-script](https://github.com/ok-oldking/ok-script) 开发您自己的自动化项目。

## 🔗 使用ok-script的项目：

* 终末地 [https://github.com/ok-oldking/ok-end-field](https://github.com/ok-oldking/ok-end-field)
* 明日方舟:终末地 [https://github.com/ok-oldking/ok-ef](https://github.com/ok-oldking/ok-end-field)
* 原神(停止维护,
  但是后台过剧情可用) [https://github.com/ok-oldking/ok-genshin-impact](https://github.com/ok-oldking/ok-genshin-impact)
* 少前2 [https://github.com/ok-oldking/ok-gf2](https://github.com/ok-oldking/ok-gf2)
* 星铁 [https://github.com/Shasnow/ok-starrailassistant](https://github.com/Shasnow/ok-starrailassistant)
* 星痕共鸣 [https://github.com/Sanheiii/ok-star-resonance](https://github.com/Sanheiii/ok-star-resonance)
* 二重螺旋 [https://github.com/BnanZ0/ok-duet-night-abyss](https://github.com/BnanZ0/ok-duet-night-abyss)
* 白荆回廊(停止更新) [https://github.com/ok-oldking/ok-baijing](https://github.com/ok-oldking/ok-baijing)


## ❤️ 赞助与致谢

### 赞助商 (Sponsors)
*   **EXE 签名**: Free code signing provided by [SignPath.io](https://signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

### 致谢
*   [ok-oldking/OnnxOCR](https://github.com/ok-oldking/OnnxOCR)
*   [zhiyiYo/PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
*   [Toufool/AutoSplit](https://github.com/Toufool/AutoSplit)