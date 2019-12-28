# -*- coding: utf-8 -*-
import json,re,os
import urllib.request, urllib.error, urllib.parse
class ZabbixAPI:
    # 初始化
    def __init__(self):
        self.__url = 'http://192.168.74.134/api_jsonrpc.php'
        self.__user = 'admin'
        self.__password = 'zabbix'
        self.__header = {"Content-Type": "application/json-rpc"}
        self.__token_id = self.UserLogin()
    # 登陆获取token
    def UserLogin(self):
        data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
        "user": self.__user,
        "password": self.__password
        },
        "id": 0,
        }
        return self.PostRequest(data)

    # 推送请求
    def PostRequest(self, data):
        request = urllib.request.Request(self.__url,json.dumps(data).encode('utf-8'),self.__header)
        result = urllib.request.urlopen(request)
        response = json.loads(result.read().decode('utf-8'))
        try:
            return response['result']
        except KeyError:
            pass

    # 获取指定模板ID名称
    def GetTemplatesID(self,Template_name):
        data = {
       "jsonrpc":"2.0",
       "method":"template.get",
       "params":{
        "output":"templateid",
        "filter": {
                "host": Template_name
                }
        },
        "auth": self.__token_id,
        "id": 0
    }
        Template_ID_List = self.PostRequest(data)
        return Template_ID_List[0]["templateid"]


    # 从指定模板ID获取所有触发器ID并返回触发器名称description
    def GetAllTriggersIDFromTemplatesID(self,Template_name):
        TemplatesID = self.GetTemplatesID(Template_name)
        data = {
         "jsonrpc": "2.0",
         "method": "trigger.get",
         "params": {
             "templateids": TemplatesID,
             "output": ["description"]
         },
        "auth": self.__token_id,
        "id": 0
    }
        return self.PostRequest(data)

    # 更新触发器名称
    def updateTriggerName(self,TriggerID=None,description=None):
        data = {
                   "jsonrpc": "2.0",
                   "method": "trigger.update",
                   "params": {
                       "triggerid": TriggerID,
                       "description": description
                   },
        "auth": self.__token_id,
        "id": 0
    }
        return self.PostRequest(data)


# 获取原触发名称，并且替换特定字符串进行批量更新触发器名称
    def ReWriteTriggerName(self,Template_name):
        StringJson = self.GetAllTriggersIDFromTemplatesID(Template_name)
        for i in range(len(StringJson)):
            ret = re.sub('已关闭', 'is down',StringJson[i]["description"])
            self.updateTriggerName(StringJson[i]["triggerid"],ret)


# 创建触发器
    def CreateTrigger(self,description=None,expression=None,recovery_expression=None):
        data = {
                   "jsonrpc": "2.0",
                   "method": "trigger.create",
                   "params": {
                        "description": description,
                        "expression": expression,
                        "priority": "4",
                        "recovery_mode": "1",
                        "recovery_expression": recovery_expression,
                        "type": "1",
                        "url": "",
                        "status": "0",
                        "correlation_mode": "0",
                        "correlation_tag": "",
                        "manual_close": "0"
                   },
        "auth": self.__token_id,
        "id": 0
    }
        return self.PostRequest(data)
# 根据所有主机的interfaceid和ip,为后续创建监控项做准备
    def GetHostID(self):
        data = {
                   "jsonrpc": "2.0",
                   "method": "host.get",
                   "params": {
                       "output":["hostid","host"],
                       "selectInterfaces":["interfaceid","ip"]
                   },
        "auth": self.__token_id,
        "id": 0
    }
        HostResult = self.PostRequest(data)
        # return HostResult["result"]
        return HostResult

    # 遍历目录下所有文件，返回完整文件路径和文件名
    def GetSourceJsonfileList(self,dir):
        filelistpath = []
        for home, dirs, files in os.walk(dir):
            for filename in files:
                fullname = os.path.join(home, filename)
                filelistpath.append(fullname)
        return filelistpath, files

    # 解析为IP地址并储存至内存
    def GetIpfromWorkDir(self,dir):
        IpList = []
        filelistpath, files = self.GetSourceJsonfileList(dir)
        # 规定正则表达式
        ss = re.compile(r'((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.){3}(1\d\d|2[0-4]\d|25[0-5]|[1-9]\d|\d)')
        for IP in files:
            IPa = ss.search(IP).group()
            IpList.append(IPa)
        return IpList

    # 格式化为json文件
    def readfile(filepath):
        with open(filepath, 'r', encoding='utf-8') as fileobject:
            json_data = fileobject.read()
            if len(json_data) > 0:
                json_datas = json.loads(json_data)
            else:
                json_datas = {}
            return json_datas
    # 获取文件夹下每个文件的内容，内容即监控项
    def GetContentFromTxt(self,dir):
        filelistpath, files = self.GetSourceJsonfileList(dir)
        for filename in filelistpath:
            with open(filename, 'r') as fileobject:
                contents = fileobject.readlines()
                for IPa in contents:
                    # 去掉左右的空格
                    name = IPa.strip()
                    key_name = IPa.strip()
                    print(name,key_name)

    # 通过传入IP返回hostid和interfaceid
    def ReturnHostIDAndInterfaceid(self,ip):
        # 判断IP
        result = self.GetHostID()
        print("result的结果是%s",  result)
        # 根据当前zabbix下所有主机IP进行判断筛选
        for i in range(len(result)):
            if result[i]["interfaces"][0]["ip"] == ip:
                return result[i]["interfaces"][0]["interfaceid"], result[i]["hostid"],result[i]["host"]

    # 添加监控项
    def AddItemsFact(self,name=None,key_=None,hostid=None,interfaceid=None):
        data = {
                "jsonrpc": "2.0",
                "method": "item.create",
                "params": {
                    "name": name,
                    "key_": key_,
                    "hostid": hostid,
                    "interfaceid": interfaceid,
                    "type": 0,
                    "value_type": 4,
                    "delay": "30s"
                },
                "auth": self.__token_id,
                "id": 0
            }
        return self.PostRequest(data)

    # 根据返回的hostip和interfaceid，将需要监控项进行批量加监控项:
    def BatchAddItem(self,dir):
        filelistpath, files = self.GetSourceJsonfileList(dir)
        iplist = self.GetIpfromWorkDir(dir)
        result = self.GetHostID()
        print("filelistpath是%s", len(filelistpath))
        for i in range(len(iplist)):
            print("i是%s",  i)
            # IP = self.GetIpfromWorkDir(dir)
            # eal_ip = IP[i]r
            # print("i1是%s", i)
            interfaceid,hostid,hostname = self.ReturnHostIDAndInterfaceid(iplist[i])
            print(hostid,interfaceid)
            # print("i2是%s", i)
            print("filelistpath是%s", filelistpath[i])
            with open(filelistpath[i], 'r') as fileobject:
                # contents = fileobject.readlines()
                # print(contents)
                for line in fileobject:
                    # 去掉左右的空格
                    name = line.strip()
                    # key_name = IPa.strip()
                    # print(name)

                    # print(result)
                    # print("result的长度是%s",  len(result))
                # 根据当前zabbix下所有主机IP进行判断筛选
                #     for j in range(len(result)):
                #         # print(real_ip)
                #         if result[j]["interfaces"][0]["ip"] == real_ip:
                #             interfaceid = result[j]["interfaces"][0]["interfaceid"]
                #             hostid = result[j]["hostid"]
                #             # print(interfaceid)
                #   print          # print(hostid)
                #     print("name1是%s", name)
                #     print("hostid1是%s", hostid)
                #     print("interfaceid1是%s", interfaceid)
                    self.AddItemsFact(name,name,hostid,interfaceid)
                    description = name + " is down"
                    expression = "{" + hostname + ":" + name + ".last()}" + "<>0"
                    recovery_expression = "{" + hostname + ":" + name + ".last()}" + "=0"
                    # 根据description,expression,recovery_expression批量添加触发器
                    self.CreateTrigger(description,expression,recovery_expression)

        # self.PostRequest(data)

#
#
def main():
#     # 实例化zabbix类
    zapi=ZabbixAPI()
    dir = r'D:\zabbix-api批量添加监控项'
#     # 模板选择
#     # hosts=zapi.ReWriteTriggerName("Template OS Linux")
#     # 添加监控项

    #prin1=zapi.GetContentFromTxt(dir)
    zapi.BatchAddItem(dir)


if __name__ == '__main__':
    main()