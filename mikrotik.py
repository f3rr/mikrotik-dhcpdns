#!/usr/bin/env python
from flask import Flask
import socket, commands
#
# Configuration
#
#
# dig binary path
dig = "/usr/bin/dig"

# nsupdate binary path
nsupdate = "/usr/bin/nsupdate"

# nsupdate key name
keyname = "nsupdate"

# nsupdate key secret
keyval = "tBoK9ec5CGBFE8VAwUKwqyKTaRidq6a1pt22r9+uFYPbLHEIpNaV8ekRm92nvooE1m3ShH60Musv2O+DGlH9Xw=="

# dns server for dig queries
dnsserver = "<DNS SERVER IP ADDRESS>"

# managed DHCP DNS zone
zone = "<DNS ZONE. EXAMPLE.COM>"

# DNS TTL (Default: 600 sec)
ttl = "600"

#
#
# Configuration end
#
# DO NOT CHANGE
#
#

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False
    return True


def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

def is_valid_address(address):
    if (is_valid_ipv4_address(address) or is_valid_ipv6_address(address)):
        return True
    else:
        return False

def get_ip_type(ip):
    if is_valid_ipv4_address(ip):
        return 'A'
    else:
        return 'AAAA'

def get_full_ptr(ip):
    i = ip.split('.')
    #return i
    return "{i4}.{i3}.{i2}.{i1}.in-addr.arpa".format(i4=i[3], i3=i[2], i2=i[1], i1=i[0])

def is_valid_hostname(host = None):
    chars = "ABCDEFGHIJKLMNOUPQRSTXYVWZabcdefghijklmnoupqrstxyvwz0987654321-"
    valid = all(c in chars for c in host)
    return valid


def host_in_dns(host):
    h = "{host}.{zone}".format(host=host,zone=zone)
    cmd = "{dig} +short {host} @{dnsserver}".format(dig=dig,host=h,dnsserver=dnsserver)
    retval,output = commands.getstatusoutput(cmd)
    if output == "":
        return False
    else:
        return True

def get_ip(host):
    h = "{host}.{zone}".format(host=host,zone=zone)
    cmd = "{dig} +short {host} @{dnsserver}".format(dig=dig,host=h,dnsserver=dnsserver)
    retval,output = commands.getstatusoutput(cmd)
    return output

def rev_in_dns(ip):
    cmd = "{dig} +short -x {ip} @{dnsserver}".format(dig=dig,ip=ip,dnsserver=dnsserver)
    retval,output = commands.getstatusoutput(cmd)
    if output == "":
        return False
    else:
        return True


app = Flask(__name__)


@app.route('/')
def home():
    return 'Mikrotik DHCP DNS Updater'


@app.route('/update/<host>/<ip>')
def update(host=None,ip=None):
    if host == None:
        return 'Something got wrong'
    else:
        if is_valid_address(ip):
            if is_valid_hostname(host):
                if host_in_dns(host): # we need to delete old entries first
                    delete(host)
                fqdn = "{host}.{zone}".format(host=host,zone=zone)
                t = get_ip_type(ip)
                ptr = get_full_ptr(ip)
                batch = [
                    'update add {fqdn} {ttl} {type} {ip}'.format(fqdn=fqdn, ttl=ttl, type=t, ip=ip),
                    '',
                    'update add {ptr} {ttl} PTR {fqdn}.'.format(ptr=ptr, ttl=ttl, fqdn=fqdn),
                    'send',
                    'quit\n'
                ]
                cmd = 'echo "{batch}" | {nsupdate} -y {keyname}:{keyval}'.format(batch='\n'.join(batch), nsupdate=nsupdate, keyname=keyname, keyval=keyval)
                #return ' '.join(batch)
                retval,output = commands.getstatusoutput(cmd)
                if retval == 0:
                    return "OK"
                else:
                    return output
            else:
            	return "Invalid hostname"
        else:
            return "Wrong IP"



@app.route('/delete/<host>')
def delete(host=None):
    if is_valid_hostname(host):
        if host_in_dns(host):
            ip = get_ip(host)
            t = get_ip_type(ip)
            fqdn = "{host}.{zone}".format(host=host,zone=zone)
            if rev_in_dns(ip):
                ptr = get_full_ptr(ip)
                batch = [
                    'update delete {ptr} PTR'.format(ptr=ptr),
                    '', #DNS BUG from 2004 new line needs to be added
                    'update delete {fqdn} {type}'.format(fqdn=fqdn,type=t),
                    'send',
                    'quit\n'
                ]
            else:
                batch = [
                    'update delete {fqdn} {type}'.format(fqdn=fqdn,type=t),
                    'send',
                    'quit\n'
                ]
            cmd = 'echo "{batch}" | {nsupdate} -y {keyname}:{keyval}'.format(batch='\n'.join(batch), nsupdate=nsupdate, keyname=keyname, keyval=keyval)
            retval,output = commands.getstatusoutput(cmd)
            if retval == 0:
                return "OK"
            else:
                return output
        else:
            return "Host not in dns"
    else:
        return "Invalid Hostname"



app.run(host='0.0.0.0')
