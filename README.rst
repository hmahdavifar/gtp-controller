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

Before starting there are 3 configuration file's that needs to be changes based on your desired topology.:
      in clients.json add client list that you need to connect to EPC.
      in controller.txt insert your sgw and pgw names and other config(names need to be written in this format 'sw'+intiger e.g. 'sw1')
      in controller.txt you need to fill out your odl controller information.



Setting up the GTP tunneling port on OVS ::
-----------------------------------------

``$ ovs-vsctl add-br br1``

# flow based tunneling port

``$ ovs-vsctl add-port br1 gtp0 -- set interface gtp0 type=gtp options:remote_ip=flow options:key=flow``

or

# port based tunneling port

``$ ovs-vsctl add-port br1 gtp1 -- set interface gtp1 type=gtp options:remote_ip=<IP of the destination> options:key=flow``



