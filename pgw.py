#!/usr/bin/python
import os
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController,OVSController
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.util import customClass
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

setLogLevel ('info')

# Two local and one "external" controller HUNG
# Ignore the warning message that remote isn't yet running

c0 = RemoteController('c0',ip='192.168.56.12')
cmap = {'sw6':c0}
#exec('~/sflow-rt/extras/sflow.py')
#exec(compile(open('/root/sflow-rt/extras/sflow.py', "rb").read(), '/root/sflow-rt/extras/sflow.py', 'exec'))
class Topology(Topo):
	def __init__(self,**opts):
		Topo.__init__(self, **opts)
		
		h6=self.addHost('h6',mac='00:00:00:00:00:16')

		
		s6=self.addSwitch('sw6')
		
		
		self.addLink(h6,s6)



class MultiSwitch (OVSSwitch):
	"Custom Switch() subclass that connects to controllers"
	def start (self,controllers):
	      return OVSSwitch.start(self,[cmap[self.name]])

topo = Topology ()
net = Mininet (topo=topo, link = TCLink, switch=MultiSwitch, build=False)
#net = Mininet (topo=topo, link = TCLink, controller=OVSController, build=False)
net.addController(c0)
net.build()
net.start()
net.staticArp()
#os.system ('sudo ifconfig sw4 192.168.60.4')
os.system ('sudo ovs-vsctl add-port sw6 tun1 -- set interface tun1 type=gre option:remote_ip=192.168.60.3')

os.system ('sudo ovs-vsctl add-port sw6 tun2 -- set interface tun2 type=gtp option:remote_ip=192.168.60.3 option:key=flow ofport_request=10')

CLI(net)
net.stop()
