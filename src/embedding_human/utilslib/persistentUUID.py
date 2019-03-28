import netifaces

def getUUID():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if interface == 'wlan0':
            return netifaces.ifaddresses('wlan0')[netifaces.AF_LINK][0]['addr'].strip(":")
        if interface == 'eth0':
            return netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0]['addr'].strip(":")
        if interface == 'en0':
            return netifaces.ifaddresses('en0')[netifaces.AF_LINK][0]['addr'].strip(":")
    return None
