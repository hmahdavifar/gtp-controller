..
      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

      Convention for heading levels in Open vSwitch documentation:

      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ~~~~~~~  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4

      Avoid deeper levels because they do not render well.

=================
Description
=================

This project resemble SDN-ECP control Plane. it configure ovs-based data Plane. it's need opendaylight controller for making changes on ovs switches and it's based on python 3, needs following packages::

      httplib2
      urllib
      json
      xml.dom.minidom
      threading

Before starting there are 3 configuration file's that needs to be changes based on your desired topology::

      in clients.json add client list that you need to connect to EPC.
      in controller.txt insert your sgw and pgw names and other config.(names need to be written in this format 'sw'+integer  e.g. 'sw1')
      in controller.txt you need to fill out your odl controller information.
      
you also need to provide 3 VMs, on 2 of them you need to install ovs from this repo https://github.com/hmahdavifar/ovs that support for gtp tunnel and also mininet for making your network topology.on last vm you should run opendaylight sdn controller.

Setting up SDN-EPC topology 
-----------------------------------------
we use virtualbox hypervisor to run this topology and it's vm, so description is based on this.
:

1. prepare ovs and mininet installed vm's as mentioned above.
2. add 2 Host-only Adapter to ovs VMs 1 in subnet range of 192.168.56.0/24 for connection to odl VM and other in subnet range on 192.168.60.0/24 for gtp tunnel.
3. set '192.168.60.3' ip add on sgw VM NIC and '192.168.60.4' on pgw NIC.
4. prepare odl installed Vm and add host-only NIC in mentioned subnet range and set '192.168.56.12' ip add on it.
5. run odl controller.
6. set ovs-host ovsdb manager to odl controller you bring up in last step.


after running this steps you should have this network:
::

    Diagram

                                                                 
                 +--------------+                                  +--------------+                  +--------------+
                 |    ovs host  |                                  |    ovs host   |                 |    odl       |
                 +--------------+                                  +---------------+                 +--------------+
 192.168.56.0/24 | eth1  | eth2 | 192.168.60.3/24   192.168.56.0/24| eth1  |  eth2 |192.168.60.3/24  |    eth1      |192.168.56.12/24
                 +--------------+                                  +---------------+                 +--------------+
                       |     |                                         |       |                            | 
                       |      ------------------------------------------       |                            |
                       --------------------------------------------------------------------------------------
                  SGW VM with OVS.                                 VM PGW with OVS.                  odl VM with opendaylight.

:
7. on sgw VM run sgw.py. it's job is to make network topology on mininet, bring up ovs bridges and configure gtp tunnel port.
8. on pgw VM run pgw.py. it's job is to make network topology on mininet, bring up ovs bridges and configure gtp tunnel port.


connecting clien's
-----------------------------------------
after the steps you.ve done so far. you have make network infrastructure bost control and data plane. now you need to program data plane to connect client's. for this we use app.py.

when you run this it's read all the configuration you provided. then it's connect to odl controller to get the epc topology. if it finds sgw and pgw in network topology it first make spanning tree of network topology based on link's utilizations to connecting clinets from SGW to out network from shortest PGW which another mininet host with '10.0.0.6' ip resemble it. until it is running it monitor network topology and maintain a STP with link utilization consideration.
after this initialization, it stop to get clinet name you like to make epc bearer for. when it get what it need. program the flows on sgw and pgw from odl and make default epc bearer flow for that client.





