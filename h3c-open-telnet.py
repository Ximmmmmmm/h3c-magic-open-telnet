#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H3C Magic 系列家用路由器 开启 Telnet 调试口(NX54 实测,固件 R014)

算法来源:开源项目 fg193/h3c-magic-telnet
    key = md5("sn=<SN>--ethaddr=<MAC>--usrpwd=<管理密码>\n--H3C.MAGIC.ZH")   # 全部小写

用法:
    python h3c-open-telnet.py <路由器IP> <SN> <MAC> <管理密码>

示例:
    python h3c-open-telnet.py 192.168.124.1 219801A3ABCDEF123456 aa:bb:cc:dd:ee:ff 你的管理密码

说明:
    MAC 填设备标签上的 MAC(基础 MAC,通常与默认 WiFi 名后缀一致,
    例如默认 WiFi 为 H3C_A1B2C3 则 MAC 是 xx:xx:xx:A1:B2:C3)。
    脚本会自动尝试该 MAC 及其后两个偏移(不同机型 WAN/LAN 偏移不同),哪个成功用哪个。
"""
import hashlib
import re
import socket
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def telnet_key(sn, mac, password):
    raw = "sn=%s--ethaddr=%s--usrpwd=%s\n--H3C.MAGIC.ZH" % (
        sn.strip().lower(), mac.lower(), password)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def mac_variants(mac):
    """基础 MAC、+1、+2 三个偏移(处理进位),外加一个无冒号写法"""
    hexs = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(hexs) != 12:
        sys.exit("MAC 格式不对:%r(需要形如 aa:bb:cc:dd:ee:ff)" % mac)
    num = int(hexs, 16)
    out = []
    for i in range(3):
        s = "%012x" % (num + i)
        out.append(":".join(s[j:j + 2] for j in range(0, 12, 2)))
    out.append(hexs.lower())
    return out


def post_telnet_debug(host, key, timeout=8):
    body = urllib.parse.urlencode({
        "CMD": "Asp_SetTelnetDebug",
        "GO": "debug_status.asp",
        "param": key,
        "location_addr": "/debug_status.asp",
    }).encode()
    req = urllib.request.Request(
        "http://%s/goform/aspForm" % host,
        data=body,
        headers={
            "User-Agent": UA,
            "Referer": "http://%s/debug_status.asp" % host,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def port_open(host, port=99, timeout=2.0):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return
    host, sn, mac, password = sys.argv[1:5]
    print("== 目标 %s ==" % host)
    if port_open(host, 99):
        print("99 端口已经是开启状态,无需重复操作")
        return
    for m in mac_variants(mac):
        code = post_telnet_debug(host, telnet_key(sn, m, password))
        ok = port_open(host, 99)
        print("  ethaddr=%s -> HTTP %s -> 99 端口:%s" % (m, code, "OPEN" if ok else "-"))
        if ok:
            print()
            print("成功!连接方式:")
            print("    telnet %s 99" % host)
            print("    输入管理密码,出现 <H3C_NX54> 提示符后输入:debugshell")
            print("    即可获得 root@OpenWrt:/# shell")
            return
    print("未成功。请检查:SN / 管理密码是否正确;MAC 是否为基础(标签)MAC。")


if __name__ == "__main__":
    main()
