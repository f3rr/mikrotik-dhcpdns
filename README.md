## Mikrotik DHCP DNS

This is project is for Mikrotik users who wants to import dhcp client names into dns. (BIND, FreeIPA, Active Directory)
The script uses dig and nsupdate for dns management and Python Flask for webserver. Mikrotik doenst list client names over snmp, and does not support dns record deletion, so we need a workaround for a proper dns management in case we have our dhcp server running on our mikrotik devices. To fix this we use a script on the mikrotik router which creates disabled static records for all dhcp leases what is used by the cleanup feature. The script will trigger dns deletion of expired/removed leases, will also track changed and add new leases into dns.


### Components
* Dockerfile
  Centos 7 Based Dockerfile, for running the Python based webserver
* mikrotik.py
  This is the webserver, and this script communicates to dns via nsupdate and dig.
* mikrotik_script.txt
  This mikrotik script triggers the webserver if dns needs to be changed based on the dhcp list


## Requirenments
* A Working DNS Setup. Any server which supports nsupdate based changes.
* A Working Mikrotik router based DHCP server setup.
* A Docker host, or optionally any host which can run python and has Flask, dig, nsupdate



## Configuration

###### mikrotik.py
* ```dig``` Path of the dig binary on the system. Defaults for linux systems
* ```nsupdate``` Path of the nsupdate binary on the system. Defaults for linux systems.
* ```keyname``` Keyname for dynamic updates configured in Bind or any other supported nameserver.
* ```keyval``` Key secret for the matching keyname.
* ```dnsserver``` The DNS Server IP address which can be queried by dig.
* ```zone``` The DNS Zone what we manage
* ```ttl``` DNS TTL to set


###### mikrotik_script.txt
* ```:local dhcpserver "defconf"``` The DHCP Server what we will manage.
* ```:local zone "<DNS-ZONE>"``` The DNS Zone what we manage.
* ```:local dnsupdater "<IP>:<PORT>"``` Python Webserver address. Put the IP of the Python Webserver and default port is 5000


## Mikrotik Script

###### Add Mikrotik script
* open Scripts under ```System / Scripts```
* add a new script via ```+``` button.
* change name (This will be used in scheduler) like ```dns-updater```
* paste mikrotik_script.txt content into source
* click ok

###### Add Scheduler
* open Scheduler under ```System / Scheduler```
* add new scheduler via ```+``` button.
* change name
* set interval to ```00:00:10``` (10 Seconds)
* put script name from before in on-event field. like ```dns-updater```
* click ok

###### Debuging
* you can debug under ```Log```.
* For enable debug add under ```System / Logging``` debug topic, or script topic.


## Docker setup
* build docker cointainer in the directory where the Dockerfile is.
  ```docker build -t mikrotik-dhcpdns .```
* run the container
  ```docker run -d -p 5000:5000 --restart unless-stopped --name mikrotik-dhcpdns mikrotik-dhcpdns```


## Standalone
* install dependencies
  * ```dns-utils``` dig and nsupdate
  * ```python-flask``` webserver
* run script
  ```./mikrotik.py```


## Bind setup (FreeIPA Supported)
* Generate Key
  ```dnssec-keygen -a HMAC-MD5 -b 512 -n HOST <key_name>```
  ```dnssec-keygen -a HMAC-MD5 -b 512 -n HOST nsupdate```
  nsupdate is in this example the key name. 
* You should end up with two new files.
  the secret is in the .private file in the line Starting with Key:
  ```Key: tBoK9ec5CGBFE8VAwUKwqyKTaRidq6a1pt22r9+uFYPbLHEIpNaV8ekRm92nvooE1m3ShH60Musv2O+DGlH9Xw==```
  This key is need in ```named.conf``` and in ```mikrotik.py```

* Edit named.conf
  ```
  key "<key_name>" {
       algorithm hmac-md5;
       secret "tBoK9ec5CGBFE8VAwUKwqyKTaRidq6a1pt22r9+uFYPbLHEIpNaV8ekRm92nvooE1m3ShH60Musv2O+DGlH9Xw==";
  };
  ```
* restart nameserver to take effect

###### FreeIPA addition steps
We need to allow the managed FreeIPA zone, to be updated by the key what we configured in the named.conf
* Go to your IPA UI ```Network Services``` than ```DNS / DNS Zones```
* Choose the managed zone, and under ```Settings``` find ```BIND Update policy``` and extend by ```grant nsupdate zonesub A; grant nsupdate zonesub AAAA; grant nsupdate zonesub TXT;```. Replace nsupdate by the key_name.



###### Reference
I took the original mikrotik script from https://www.tolaris.com/2014/09/27/synchronising-dhcp-and-dns-on-mikrotik-routers/
That script can be used to have status DNS entries without external DNS server.