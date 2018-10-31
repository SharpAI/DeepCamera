# -*- coding: utf-8 -*-
import xml.sax
from syncthing import Syncthing
import time

class xmlHandler( xml.sax.ContentHandler ):
    def __init__(self):
        self.currentkeyName = ""
        self.apikey = ""
    def startElement(self, tag, attributes):
        if tag == 'apikey':
            self.currentkeyName = "apikey"
            #print("begain to parse %s"%(tag))
    def endElement(self, tag):
        if tag == 'apikey':
            self.currentkeyName = ""
            #print("finised parsing %s"%(tag))
    def characters(self, content):
        if len(self.currentkeyName) > 1 and self.currentkeyName == "apikey":
            #print("%s=%s"%(self.currentkeyName, content))
            self.apikey = str(content)

def get_Current_Syncthing_apikey(cfg_file):
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Handler = xmlHandler()
    parser.setContentHandler( Handler )
    parser.parse(cfg_file)
    if len(Handler.apikey) < 1:
        print('apikey not found !')
    return Handler.apikey


class workaiSynctingClass:
    def __init__(self):
        self.KEY  = ''
        self.HOST = '127.0.0.1'
        self.PORT = 8384
        self.IS_HTTPS = False
        self.SSL_CERT_FILE = None
        self.syncthing = None
        self.syncthing_myID = None

    def _get_status(self):
        if self.syncthing is None:
            return None
        status = self.syncthing.system.status()
        if type(status) == str:
            status = json.loads(status)
        myId = status.get("myID", "")
        if len(myId) > 1:
            self.syncthing_myID = myId

    def _get_discovery_IDs(self):
        IDs = []
        if self.syncthing is None:
            return None
        discovery = self.syncthing.system.discovery()
        for key in discovery:
            IDs.append(key)
        print('discovery:')
        print(IDs)

    def _get_connections_IDs(self):
        IDs = []
        if self.syncthing is None:
            return None
        connections = self.syncthing.system.connections()
        for key in connections['connections']:
            IDs.append(key)
        print('connections:')
        print(IDs)

    def _get_config(self):
        if self.syncthing is None:
            return None
        config = self.syncthing.system.config()
        print(config)

    def add_one_device_to_syncthing(self, deviceId):
        if self.syncthing is None or len(deviceId) < 1:
            return None
        config = self.syncthing.system.config()
        if config is None:
            return None
        devices = config['devices']
        if config is None:
            return None
        for device in devices:
            if device['deviceID'] == deviceId:
                print("%s: this device already added !" %(device['deviceID']))
                return None

        new_device = {
            u'compression': u'metadata',
            u'skipIntroductionRemovals': False,
            u'allowedNetworks': [],
            u'certName': u'',
            u'introducer': False,
            u'name': u'',
            u'paused': False,
            u'deviceID': deviceId,
            u'introducedBy': u'',
            u'addresses': [u'dynamic']
        }

        devices.append(new_device)
        config['devices'] = devices

        #把添加过设备的配置文件发回syncthing
        self.syncthing.system.set_config(config, and_restart=False)
        print("%s device added !" %(deviceId))
        return new_device

    def remove_one_device_from_syncthing(self, deviceId):
        hasRemoved = True
        devices_new = []

        if self.syncthing is None or len(deviceId) < 1:
            return None
        config = self.syncthing.system.config()
        if config is None:
            return None
        devices = config['devices']
        if config is None:
            return None
        for device in devices:
            if device['deviceID'] != deviceId:
                devices_new.append(device)
            else:
                hasRemoved = False

        if hasRemoved is True:
            print("%s: this device already removed !" %(device['deviceID']))
            return None

        config['devices'] = devices_new
        #把添加过设备的配置文件发回syncthing
        self.syncthing.system.set_config(config, and_restart=False)
        print("%s device removed !" %(deviceId))
        return devices_new


    def initialize(self, configFile):
        self.KEY  = get_Current_Syncthing_apikey(configFile)

        self.syncthing = Syncthing(self.KEY, self.HOST, self.PORT, 10.0, self.IS_HTTPS, self.SSL_CERT_FILE)
        # name spaced by API endpoints
        self.syncthing.system.connections()

        # suports GET/POST semantics
        sync_errors = self.syncthing.system.errors()
        self.syncthing.system.clear()

        if sync_errors:
            for e in sync_errors:
                print(e)

        #self.syncthing.system.disable_debug()

        #self._get_status()
        #self._get_discovery_IDs()
        #self._get_connections_IDs()
        #self._get_config()

#if __name__ == '__main__':
#    sync = workaiSynctingClass()
#    sync.initialize('./config.xml')
#    sync.add_one_device_to_syncthing('OUDMQHI-WWYFDIB-FYBLKTX-K2VZDMH-BLAPIO3-MLAUPFS-QYI3RIC-IH6KUQG')
#    time.sleep(10)
#    sync.remove_one_device_from_syncthing('OUDMQHI-WWYFDIB-FYBLKTX-K2VZDMH-BLAPIO3-MLAUPFS-QYI3RIC-IH6KUQG')
