#!/usr/bin/python
import os
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
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
cmap = {'sw1':c0,'sw2':c0,'sw3':c0,'sw4':c0,'sw5':c0}
#exec('~/sflow-rt/extras/sflow.py')
exec(compile(open('/root/sflow-rt/extras/sflow.py', "rb").read(), '/root/sflow-rt/extras/sflow.py', 'exec'))
class Topology(Topo):
	def __init__(self,**opts):
		Topo.__init__(self, **opts)
		h1=self.addHost('h1',mac='00:00:00:00:00:11')
		h2=self.addHost('h2',mac='00:00:00:00:00:12')
		h3=self.addHost('h3',mac='00:00:00:00:00:13')
		h4=self.addHost('h4',mac='00:00:00:00:00:14')
		h5=self.addHost('h5',mac='00:00:00:00:00:15')
		
		h7=self.addHost('h7',mac='00:00:00:00:00:17')
		h8=self.addHost('h8',mac='00:00:00:00:00:18')
		s1=self.addSwitch('sw1')
		s2=self.addSwitch('sw2')
		s3=self.addSwitch('sw3')
		s4=self.addSwitch('sw4')
		s5=self.addSwitch('sw5')
		
		self.addLink(h1,s1)
		self.addLink(h2,s2)
		self.addLink(h3,s3)
		self.addLink(h4,s4)
		self.addLink(h5,s5)
		self.addLink(h7,s5)
		self.addLink(h8,s5)
		
		self.addLink(s1,s2,bw=10)
		self.addLink(s1,s3,bw=10)
		self.addLink(s2,s4,bw=10)
		self.addLink(s3,s4,bw=10)
		self.addLink(s1,s4,bw=10)
		self.addLink(s1,s5,bw=10)
		

class MultiSwitch (OVSSwitch):
	"Custom Switch() subclass that connects to controllers"
	def start (self,controllers):
	      return OVSSwitch.start(self,[cmap[self.name]])

topo = Topology ()
net = Mininet (topo=topo, link = TCLink, switch=MultiSwitch, build=False)
net.addController(c0)
net.build()
net.start()
net.staticArp()
#os.system ('sudo ifconfig sw4 192.168.60.3')

os.system ('sudo ovs-vsctl add-port sw4 tun1 -- set interface tun1 type=gre option:remote_ip=192.168.60.4')
os.system ('sudo ovs-vsctl add-port sw4 tun2 -- set interface tun2 type=gtp option:remote_ip=192.168.60.4 option:key=flow ofport_request=10')
CLI(net)
net.stop()
