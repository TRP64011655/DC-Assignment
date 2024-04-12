import netifaces as ni

MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5005

def get_ip_address():
    interfaces = ni.interfaces()
    for interface in interfaces:
        try:
            ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
            if not ip.startswith("127.") and not ip.startswith("169."):
                return ip
        except KeyError:
            pass
    return None