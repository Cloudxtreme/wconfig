#!/usr/bin/env python
import sys
import gobject
import getopt
import time
import os
import wicd
from wicd import dbusmanager
from dbus import DBusException

# connection to DBUS interface
try:
    dbusmanager.connect_to_dbus()
except DBusException:
        print "Cannot connect to WICD daemon, please be sure daemon is started before using wconfig. You can start daemon with /etc/init.d/wicd start, or /etc/rc.d/wicd start, or wicd from root account."
        sys.exit()

bus = dbusmanager.get_bus()
dbus_ifaces = dbusmanager.get_dbus_ifaces()
daemon = dbus_ifaces['daemon']
wireless = dbus_ifaces['wireless']
[state, info] = daemon.GetConnectionStatus()

# CONFIG
output_as = "Text" # default, also XML avaible
autoconnect = False # try to connect if found a unsecured network
extra_debugging = False
network_timeout = 30

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:m:e:hdaxsg", ["help", "auto-connect", "xml", "scan", "debug", "--connect-by-id", "--connect-by-mac", "--connect-by-name"]) # output=

	except getopt.GetoptError, err:
		print "Error: "+str(err)+", Try --help for usage\n\n"
		# usage()
		sys.exit(2)
	
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		if o in ("-a", "--auto-connect"):
			global autoconnect
			autoconnect = True
		if o in ("-g", "--debug"):
			global extra_debugging
			extra_debugging = True
		if o in ("-x", "--xml"):
			global output_as
			output_as = "XML"
                if o in ("-d", "--disconnect"):
                        if len(info) > 2:
                                wireless.DisconnectWireless()

			time.sleep(5)

                if o in ("-i", "--connect-by-id"):
			connectById(a)

                if o in ("-m", "--connect-by-mac"):
			connectByAttr(a, 'bssid')
                if o in ("-e", "--connect-by-name"): # b - essid
			connectByAttr(a, 'essid')
                        #sys.exit() # continue scanning
		if o in ("-s", "--scan"):
			scan()

	if len(opts) == 0:
            print "Wconfig - simple WICD client for GNU/Linux written in Python, supports XML output."
            print "No arguments specified, see wconfig --help"
          

def connectByAttr(value, attr):
    """ Find a wireless network by attribute eg. mac adress or bssid and connect to it """
    num_networks = wireless.GetNumberOfNetworks()
    Found = False
    print value
    if num_networks > 0:
        for x in range(0, num_networks):
            if get_prop(x, attr) == value:
                connectById(x)
                Found = True

    if Found == False:
        if output_as == "XML":
            print "<?xml version=\"1.0\" encoding=\"UTF-8\"?><message>Wireless network not found</message>"
        else:
            print "Network not found."
    else:
        if extra_debugging == True:
           print "Connected to network using "+str(attr)+"=\""+str(value)+"\""


def connectById(a):
        """ Connect to wireless network by id """
        global info, extra_debugging

        try:
            i = int(a)
        except ValueError:
            print "ERROR: -i (--connect-by-id) should be numeric"
            sys.exit()

        num_networks = wireless.GetNumberOfNetworks()

        if i <= num_networks:
            wireless.ConnectWireless(int(i))

            essid = str(get_prop(i, "essid"))

            if extra_debugging == True:
                print "Connecting to "+essid

            while len(info) < 3:
                i += 1
                if i > network_timeout: # timeout - X seconds for one connection
                    break

                if extra_debugging == True:
                    print "Sleeping "+str(i)+"s for network "+essid

                time.sleep(1) # wait one second for wicd daemon
                [state, info] = daemon.GetConnectionStatus()

            if len(info) <3:
                print "ERROR: Cannot connect to wireless network"
        else:
            print "ERROR: Network not found."





def usage():
	'Shows program usage and version, lists all options'

	print "wconfig for GNU/Linux, a wireless scanner with option to connect automaticaly to wireless, provide also XML output"
	print "Usage: wconfig [long GNU option] [option]"
	print ""
	print " --xml, -x - output results as XML to be easy to parse"
	print " --auto-connect, -a - output results as XML to be easy to parse"
	print " --debug, -g - enable extra debugging"
	print " --disconnect, -d - disconnect from network if connected"
	print " --connect-by-mac, -m - connect to wireless network by mac adress"
	print " --connect-by-name, -e - connect to wireless network name (essid)"
	print " --help, -h this screen"
        print ""
        print "Examples:"
        print " wconfig -s # scan for wireless networks and show results as plaintext"
        print " wconfig -xs # scan for wireless networks and show results as parsable XML"
        print " wconfig -d # disconnect from wireless network"
        print " wconfig -ds # disconnect from wireless network and scan for network"
        print " wconfig -m 00:00:00:00:00:00 # connect to wireless network by MAC adress"
        print " wconfig -e my-network # connect to wireless network by bssid (network name)"
        print " wconfig -i 0 # connect to first network from list, to list networks type wconfig -s"
        print " wconfig -as # connect to first working network"

def get_prop(net_id, prop):
        """ Get attribute of wireless network """
        return wireless.GetWirelessProperty(net_id, prop)

def fix_strength(val, default):
        """ Assigns given strength to a default value if needed. """
        return val and int(val) or default

def scan():
        """ Scan for local wireless network, output to stdout as plaintext or XML """
        global extra_debugging
        global info
        global network_timeout

        num_networks = wireless.GetNumberOfNetworks()
	
        if num_networks > 0:

		networks = {}
                connected = False

                for x in range(0, num_networks):
                    essid = get_prop(x, "essid")
                    encryption = str(get_prop(x, "encryption_method"))
                    networks[x] = {}

                    if len(info) > 2:
                            connected = True
                            if info[1] == essid:
                                networks[x]['active'] = "*ACTIVE*"
                            else:
                                networks[x]['active'] = ""
                    else:
                            networks[x]['active'] = ""


                   # try to connect to network, refresh state about networks
                    if connected == False and autoconnect == True:
                            wireless.ConnectWireless(x)
                            [state, info] = daemon.GetConnectionStatus()
                            i=0

                            if extra_debugging == True:
                                print "Connecting to "+essid

                            while len(info) < 3:
                                    i += 1
                                    if i > network_timeout: # timeout - X seconds for one connection
                                        break

                                    if extra_debugging == True:
                                        print "Sleeping "+str(i)+"s for network "+essid

                                    time.sleep(1) # wait one second for wicd daemon
                                    [state, info] = daemon.GetConnectionStatus()

                            if len(info) > 2:
                                    connected = True
                                    networks[x]['active'] = "*ACTIVE*"


                    networks[x]['name'] = essid
                    networks[x]['strength'] = fix_strength(get_prop(x, "quality"), -1)
                    networks[x]['encryption'] = encryption
                    networks[x]['mode'] = get_prop(x, 'mode')
                    networks[x]['channel'] = get_prop(x, 'channel')
                    networks[x]['bssid'] = get_prop(x, 'bssid')

                if output_as == "XML":
                        outputScanAsXML(networks)
                else:
                        outputScanAsText(networks)
	else:
		print "No wireless networks found."

def outputScanAsText (listOfNetworks):
        """ Output scan results as plaintext """

	for line in listOfNetworks:
                print str(line)+ " "+str(listOfNetworks[line]['bssid'])+" \""+str(listOfNetworks[line]['name'])+"\" "+str(listOfNetworks[line]['encryption'])+" "+str(listOfNetworks[line]['strength'])+"% "+str(listOfNetworks[line]['mode'])+" "+str(listOfNetworks[line]['channel'])+" "+listOfNetworks[line]['active']

def outputScanAsXML (listOfNetworks):
        """ Output scan results as parsable XML """
        print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        print "<networks>"
	for line in listOfNetworks:
                print "   <network>"
		print "        <mac>"+str(listOfNetworks[line]['bssid'])+"</mac>"
		print "        <name>"+str(listOfNetworks[line]['name'])+"</name>"
		print "        <encryption>"+str(listOfNetworks[line]['encryption'])+"</encryption>"
		print "        <percentage_strength>"+str(listOfNetworks[line]['strength'])+"</percentage_strength>"
		print "        <mode>"+str(listOfNetworks[line]['mode'])+"</mode>"
		print "        <channel>"+str(listOfNetworks[line]['channel'])+"</channel>"

		if listOfNetworks[line]['active'] == "*ACTIVE*":
		        print "        <active>True</active>"
                else:
		        print "        <active>False</active>"
                print "   </network>"

        print "</networks>"


if __name__ == "__main__":
    main()
