#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from math import floor
from random import random

try:
    from enum import Enum
    import argparse
    import json
    import requests
    import urllib3
    import time
    import hashlib
    import base64
    import rsa

    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

except ImportError as e:
    print("Missing python module: {}".format(e.message))
    sys.exit(255)


class NagiosState(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class CheckNetgear:
    options = {}

    def outputVerbose(self, msg):
        if self.options.verbose:
            print(msg)

    def outputStatus(self, status, msg, perfData):
        ret = "Status: " + status.name
        if len(msg) > 0:
            ret += " - " + msg
        if perfData is not None:
            ret += " | " + perfData
        print(ret)
        sys.exit(status.value)

    def nowMillis(self):
        return int(time.time() * 1000)

    def addUrlHash(self, url):
        url += "&bj4=" + hashlib.md5(url.split("?")[1].encode()).hexdigest()
        return url

    def buildURL(self, url):
        return "http://" + self.options.hostname + "/" + self.addUrlHash(url)

    def getLogin(self):
        url = self.buildURL("cgi/get.cgi?cmd=home_login&aj4=" + str(self.nowMillis()))

        self.outputVerbose("Get " + url + "...")
        res = requests.get(
            url,
            verify=False
        )
        self.outputVerbose("...done. (" + str(res.status_code) + ")")

        if res.status_code == 200:
            return res.json()
        else:
            return None

    def doLogin(self, pwdHash):
        url = self.buildURL("cgi/set.cgi?cmd=home_loginAuth&dummy=" + str(self.nowMillis()))
        obj = {"_ds=1&pwd=" + pwdHash + "&actKeyText=&xsrf=null&_de=1": {}}

        self.outputVerbose("Post " + url + "...")
        res = requests.post(
            url,
            json=obj
        )
        self.outputVerbose("...done. (" + str(res.status_code) + ")")

        if res.status_code == 200:
            self.outputVerbose(res.json())
            return res.json()
        else:
            self.outputVerbose(res.json())
            return None

    def getLoginStatus(self, authId):
        url = self.buildURL("cgi/set.cgi?cmd=home_loginStatus&dummy=" + str(self.nowMillis()))
        obj = {
            "_ds=1&authId=" + authId + "&xsrf=null&_de=1": {}
        }

        self.outputVerbose("Post " + url + "...")
        res = requests.post(
            url,
            json=obj
        )
        self.outputVerbose("...done. (" + str(res.status_code) + ")")

        if res.status_code == 200:
            self.outputVerbose(res.json())
            return res
        else:
            self.outputVerbose(res.json())
            return None

    def parseSession(self, res):
        if res is not None and res.json()["data"]["status"] == "ok":
            sess = base64.b64decode(res.json()["data"]["sess"])
            cookie = res.headers.get("Set-Cookie")
            return dict(tabId=sess[0:32], expo=sess[32:37], modulus=sess[37:len(sess) - 1], cookie=cookie)

        return None

    def encode(self, input):
        text = ""
        possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        l = len(input)
        ln = len(input)

        for i in range(1, 320 - l, 1):
            if 0 == i % 7 and l > 0:
                l -= 1
                text += input[l]
            elif i == 123:
                if ln < 10:
                    text += 0
                else:
                    text += str(floor(ln / 10))
            elif i == 289:
                text += str(ln % 10)
            else:
                text += possible[floor(random() * len(possible))]

        return text

    def encryptStr(self, msg, modulus):
        key = rsa.PublicKey(int.from_bytes(bytes.fromhex(modulus.decode("utf-8")), byteorder="big"), int("10001", 16))
        return base64.b64encode(rsa.encrypt(msg, key))

    def getData(self, cmd, session):
        url = self.buildURL("cgi/get.cgi?cmd=" + cmd + "&dummy=" + str(self.nowMillis()))

        self.outputVerbose("Get " + url + "...")
        res = requests.get(
            url,
            verify=False,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-CSRF-XSID": self.encryptStr(session["tabId"], session["modulus"]),
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": session["cookie"]
            }
        )
        self.outputVerbose("...done. (" + str(res.status_code) + ")")

        if res.status_code == 200:
            self.outputVerbose(res.json())
            return res.json()
        else:
            try:
                self.outputVerbose(res.json())
            except:
                self.outputVerbose(res)
            return None

    def parseOptions(self):
        p = argparse.ArgumentParser(description="Check command Netgear")

        api_opts = p.add_argument_group("API Options")

        api_opts.add_argument("-H", "--hostname", required=True, help="hostname or ip address")
        api_opts.add_argument("-P", "--password", required=True, help="password")
        api_opts.add_argument("-v", "--verbose", dest="verbose", action="store_true", default=False,
                              help="verbose output")

        check_opts = p.add_argument_group("Check Options")

        check_opts.add_argument("-wT", "--warningThermal", dest="threshold_warning_thermal", type=int, default=50,
                                help="Warning threshold for thermal value")
        check_opts.add_argument("-cT", '--criticalThermal', dest="threshold_critical_thermal", type=int, default=70,
                                help="Critical threshold for thermal value")
        check_opts.add_argument("-wF", "--warningFan", dest="threshold_warning_fan", type=int, default=90,
                                help="Warning threshold for fan duty value (percent)")
        check_opts.add_argument("-cF", '--criticalFan', dest="threshold_critical_fan", type=int, default=100,
                                help="Critical threshold for fan duty value (percent)")
        check_opts.add_argument("-wM", "--warningMemory", dest="threshold_warning_memory", type=int, default=80,
                                help="Warning threshold for memory (percent)")
        check_opts.add_argument("-cM", '--criticalMemory', dest="threshold_critical_memory", type=int, default=90,
                                help="Critical threshold for memory (percent)")

        options = p.parse_args()

        self.options = options

    def checkNetgear(self):
        loginInfo = self.getLogin()
        if loginInfo is not None:
            model = loginInfo["data"]["model"]
            if not (model in ["GS724TPv3"]):
                self.outputStatus(NagiosState.UNKNOWN, "Unsupported model {0}".format(model), None)

        status = NagiosState.OK
        session = None
        err_msg = None
        success = False
        retry = 0

        while retry < 5 and not success:
            login = self.doLogin(self.encode(self.options.password))

            if login is None:
                status = NagiosState.UNKNOWN
                err_msg = "Couldn't login to switch."
                retry += 1
                time.sleep(1 * retry)
                self.outputVerbose("do login - retry " + str(retry + 1) + "...")
                continue

            # wait before logged in
            time.sleep(0.1)

            session = self.parseSession(self.getLoginStatus(login["authId"]))

            if session is None:
                status = NagiosState.UNKNOWN
                err_msg = "Couldn't get a session."
                retry += 1
                time.sleep(1 * retry)
                self.outputVerbose("get session - retry " + str(retry + 1) + "...")
                continue

            success = True

        if not success:
            self.outputStatus(status, err_msg, None)

        status = NagiosState.OK

        sysInfo = self.getData("sys_info", session)
        if not sysInfo is None:
            thermals = sysInfo["data"]["thermals"];
            fans = sysInfo["data"]["fans"]

            msg = [
                "{0} ({1}) {2}".format(sysInfo["data"]["sysName"], sysInfo["data"]["sysSN"],
                                       sysInfo["data"]["txtSwVer"])]
            perf_data = []

            for ti in range(0, len(thermals)):
                t = thermals[ti]["temp"]

                if self.options.threshold_warning_thermal < t < self.options.threshold_critical_thermal:
                    status = NagiosState.WARNING
                if t > self.options.threshold_critical_thermal:
                    status = NagiosState.CRITICAL

                msg.append("Thermal ({0}) {1}C".format(str(ti + 1), str(t)))
                perf_data.append("'Thermal-{0}'={1}C;0:{2};0:{3}".format(str(ti + 1), str(t),
                                                                         self.options.threshold_warning_thermal,
                                                                         self.options.threshold_critical_thermal))

            for fi in range(0, len(fans)):
                speed = fans[fi]["txtFanSpeed"]
                duty = fans[fi]["txtDutyLevel"]

                if self.options.threshold_warning_fan < t < self.options.threshold_critical_fan:
                    status = NagiosState.WARNING
                if t >= self.options.threshold_critical_fan:
                    status = NagiosState.CRITICAL

                sW = round(speed / duty * self.options.threshold_warning_fan)
                sC = round(speed / duty * self.options.threshold_critical_fan)

                msg.append("Fan ({0}) {1}rpm ({2}%)".format(str(fi + 1), str(speed), str(duty)))

                perf_data.append("'Fan-{0} Speed'={1};{2};{3}".format(str(fi + 1), str(speed), sW, sC))
                perf_data.append("'Fan-{0} Duty'={1}%;{2};{3};0;100".format(str(fi + 1), str(duty),
                                                                            self.options.threshold_warning_fan,
                                                                            self.options.threshold_critical_fan))

        sysCpuStatus = self.getData("sys_cpu_status", session)
        if not sysCpuStatus is None:
            sysInfo = sysCpuStatus["data"]
            if sysInfo is not None:
                total = int(sysInfo["totalSysMem"])
                alloc = sysInfo["allocMem"]

                mp = round(100 / total * alloc)
                mW = round(total / 100 * self.options.threshold_warning_memory)
                mC = round(total / 100 * self.options.threshold_critical_memory)

                if mW < alloc < mC:
                    status = NagiosState.WARNING
                if alloc > mC:
                    status = NagiosState.CRITICAL

                msg.append("Memory {0}/{1} ({2}%)".format(alloc, total, mp))

                perf_data.append(
                    "'Memory'={0};{1};{2};0;{3}".format(alloc, mW, mC, total))

        poeInfo = self.getData("home_view", session)
        if not poeInfo is None:
            units = poeInfo["data"]["units"]
            if units is not None:
                for ui in range(0, len(units)):
                    cp = float(poeInfo["data"]["units"][ui]["consumedPower"])
                    np = float(poeInfo["data"]["units"][ui]["nominalPower"])
                    tp = float(poeInfo["data"]["units"][ui]["thresholdPower"])

                    if tp < cp < np:
                        status = NagiosState.WARNING
                    if cp > np:
                        status = NagiosState.CRITICAL

                    msg.append(
                        "Consumed Power{0} {1}W/{2}W".format("" if len(units) == 1 else " (" + str(ui + 1) + ")",
                                                             str(cp),
                                                             str(np)))

                    perf_data.append(
                        "'Consumed Power{0}'={1}W;{2};{3};0;{3}".format("" if len(units) == 1 else " " + str(ui + 1),
                                                                        str(cp), str(tp), str(np)))

        self.outputStatus(status, ", ".join(str(x) for x in msg), " ".join(str(x) for x in perf_data))

    def check(self):
        self.parseOptions()
        self.checkNetgear()


netgear = CheckNetgear()
netgear.check()
