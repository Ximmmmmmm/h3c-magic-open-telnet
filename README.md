# h3c-magic-open-telnet

H3C Magic 系列家用路由器 **一键开启 Telnet 调试口**的脚本与实测教程(2026-10,NX54 实测)。

开启后通过 telnet 登录、输入 `debugshell`,即可获得 **root shell**(`root@OpenWrt:/#`)。

- **零依赖**:只需要 Python 3,无第三方库
- **参数化**:SN / MAC / 管理密码全部命令行传入,脚本不含任何硬编码
- **自动容错**:自动尝试 MAC 的三个偏移,适配不同机型的 WAN/LAN MAC 布局
- **附带关闭方法**:收录「用完如何彻底关闭」的完整流程(大多数教程只讲开不讲关)
- 算法来源:[fg193/h3c-magic-telnet](https://github.com/fg193/h3c-magic-telnet)

> ⚠️ **仅限操作自有设备**,并请阅读文末[风险与免责](#风险与免责)。

---

## 适用机型

| 机型 | 固件 | 实测状态 |
|---|---|---|
| H3C NX54 | `NX54V100R014` | ✅ 实测可用(2026-10) |
| H3C Magic 系列其他机型(NX15 / NX30 / RC3000 / RW3000 等) | — | 理论适用(接口与算法通用),**未逐一实测**,欢迎反馈 |

## 快速开始

### 0. 准备三样东西

| 需要 | 从哪获取 |
|---|---|
| **SN**(序列号) | 底部标签;或登录后台访问 `http://192.168.124.1/maintain_basic.asp`,源码里搜 `ui_sn` |
| **MAC**(基础 / WAN MAC) | 底部标签;**最直观:与默认 WiFi 名后缀一致**——默认 WiFi 为 `H3C_A1B2C3`,则 MAC 为 `xx:xx:xx:A1:B2:C3` |
| **管理密码** | Web 后台登录密码(不是 WiFi 密码) |

### 1. 运行脚本

```bash
python h3c-open-telnet.py 192.168.124.1 <你的SN> <你的MAC> <你的管理密码>
```

成功时输出:

```
== 目标 192.168.124.1 ==
  ethaddr=xx:xx:xx:a1:b2:c3 -> HTTP 200 -> 99 端口:OPEN

成功!连接方式:
    telnet 192.168.124.1 99
    输入管理密码,出现 <H3C_NX54> 提示符后输入:debugshell
    即可获得 root@OpenWrt:/# shell
```

### 2. 连接并进入 root

```bash
telnet 192.168.124.1 99      # 提示 Password: 时输入管理密码
```

出现 `<H3C_NX54>` 提示符后输入:

```
debugshell
```

得到 `root@OpenWrt:/#`,验证:

```bash
id                           # 应输出 uid=0(root)
```

> **Windows 没有 telnet 命令?** 「控制面板 → 程序 → 启用或关闭 Windows 功能」勾选「Telnet 客户端」;或用 PuTTY / Xshell / WSL,端口填 `99`。

## 原理

H3C Magic 系列固件内置售后调试接口 `Asp_SetTelnetDebug`(位于 `/goform/aspForm`),提交正确密钥后即拉起 `telnetd`(监听 99 端口):

```
key = md5("sn=<SN>--ethaddr=<WAN MAC>--usrpwd=<管理密码>\n--H3C.MAGIC.ZH")   # 全部小写
```

- 密钥算法来自开源项目 [fg193/h3c-magic-telnet](https://github.com/fg193/h3c-magic-telnet)(Rust 实现);
- 本仓库提供 Python 参数化版,并自动尝试 MAC 偏移以提高成功率。

## 用完如何关闭(建议阅读)

长期开着调试口会多一个入口,建议用完关闭(root shell 下操作):

**方法一(临时)**:`killall telnetd`
> 重启后可能恢复(接口会写入启动配置,实测重启后仍开启)。

**方法二(彻底)**:
1. **先备份**配置(后台导出备份,或直接保留一份 `/mnt/cfg/startup`);
2. 编辑 `/mnt/cfg/startup`:`telnetenable=enable` → `disable`;顺手将 `remote_telnet_en=1` → `0`;
3. **重算文件首行 MD5**:第 1 行格式为 `<md5>  /var/run/.tmpcfg`(51 字节含换行),
   md5 值 = **从第 2 行起到文件末尾全部字节**的 md5;文件为纯 LF 换行;
4. 写回后 `killall telnetd`,重启路由器,验证 99 端口不再监听。

> ⚠️ **该配置包含宽带拨号账号等关键信息,格式或 md5 写错会触发固件恢复默认配置(宽带账号丢失)**。务必先备份、逐字节校验后再重启;没有把握时不要改文件,直接用方法一临时关闭。

## FAQ

**Q:运行后 99 端口没开?**
A:依次检查:① SN / 管理密码是否正确;② MAC 是否用标签上的基础 MAC(脚本会自动试 +0/+1/+2 偏移);③ 路由器 IP 是否正确。

**Q:管理密码是 WiFi 密码吗?**
A:不是。是登录 Web 后台的密码。

**Q:重启后 telnet 还在吗?**
A:在(实测)。接口会写入启动配置,重启后仍然开启;彻底关闭见上一节。

**Q:拿到 root 能做什么?**
A:读写路由器全部配置(DNS、DHCP、iptables 等)、部署自定义服务(如透明代理)等。root 下误操作风险自负。

**Q:固件升级后还能用吗?**
A:未验证。接口行为可能随固件更新变化,以最新实测为准。

## 参考

- [fg193/h3c-magic-telnet](https://github.com/fg193/h3c-magic-telnet) —— 算法来源与一键开启工具,适用于 H3C Magic 系列
- 恩山论坛 H3C 板块相关讨论帖

## 风险与免责

- 本文方法基于厂商固件内置调试接口与开源算法,仅供**自有设备**研究学习;请勿用于未经授权的设备。
- root 权限可读写全部配置,误操作可能导致配置丢失甚至设备无法启动;操作前请做好备份。
- 调试口仅在内网监听且需要密码登录,但长期开启仍会扩大攻击面,建议用完关闭。
- 开启调试功能可能影响保修;固件升级后可能失效。
- 使用本工具即表示你已知晓并自行承担上述风险。

## License

[MIT](LICENSE)
