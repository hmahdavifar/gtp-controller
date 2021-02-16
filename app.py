import os
import socket
import subprocess
import sys
from datetime import datetime
import httplib2
import urllib.parse
import json
import xml.dom.minidom
import graphviz
from IPython.display import display
import xml.dom.minidom as DOM
from urllib.parse import urlencode
import pickle
import json
from collections import defaultdict
import time
import threading
import argparse
from random import randrange

# COLLECTOR_IP = 'http://192.168.56.12:8181'
# COLLECTOR_PORT = '8181'
# TIME_INTERVAL = '15'




class myThread (threading.Thread):
    exitFlag = 0
    def __init__(self, remote,threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.remote = remote

    def run(self):
        print ("Starting " + self.name) 
        if self.name == 'port_monitor':
            time.sleep(10)
            while not myThread.exitFlag:
                for k in self.remote.nodes.keys():
                    for port,att in self.remote.nodes[k]['port'].items():
                        if not any('tun' in s for s in att.keys()):
                            num = k.replace('sw','')
                            byte = self.remote.query_port_statistics('openflow:'+num+':'+port)
                            cs = self.remote.query_port_current_speed('openflow:'+num+':'+port)
                            util = 80 *(int(byte) - int(att['openflow:'+num+':'+port]['txbyte']))/int(cs)

                            if util <= 80:
                                self.remote.nodes[k]['port'][port]['openflow:'+num+':'+port]['port_prio'] = 1
                            else:
                                self.remote.nodes[k]['port'][port]['openflow:'+num+':'+port]['port_prio'] = 2


                time.sleep(10)
            
                
        print ("Exiting " + self.name)

class Flow:
    def __init__(self, flowname, sw):
        
        self.flowname = flowname
        self.sw = sw
        

class GateWay:
    def __init__(self, name = '' , ofname = '', ovsdbname = '', tueip = '', mac = '', services = []):
        self.name = name
        self.mac = mac
        self.tueip = tueip
        self.ofname = ofname
        self.ovsdbname = ovsdbname
        self.services = {}
        self.flows = {}
        for service in services:
            self.services[service['name']] = service['service']
            
class Stp:
    def __init__(self,nodenum):
        self.V = nodenum 
        self.graph = []
    def addedge(self, u, v, w):
        self.graph.append([u, v, w])
    def find(self, parent , i):
        if parent[i] == i:
            return i
        return self.find(parent, parent[i])
    def union(self, parent, rank, x, y):
        xroot = self.find(parent, x)
        yroot = self.find(parent, y)
        if rank[xroot] < rank[yroot]:
            parent[xroot] = yroot
        elif rank[xroot] > rank[yroot]:
            parent[yroot] = xroot
        else:
            parent[yroot] = xroot
            rank[xroot] += 1
    def KruskalMST(self):
        result = []
        i = 0
        e = 0
        self.graph = sorted(self.graph,key=lambda item: item[2])
        parent = []
        rank = []
        for node in range(self.V):
            parent.append(node)
            rank.append(0)
        while e < self.V - 1:
            u, v, w = self.graph[i]
            i = i + 1
            x = self.find(parent, u)
            y = self.find(parent, v)
            if x != y:
                e = e + 1
                result.append([u, v, w])
                self.union(parent, rank, x, y)
        minimumCost = 0
        print ("Edges in the constructed MST")
        for index, edge in enumerate(result):
            result[index][0]+=1
            result[index][1]+=1
            minimumCost += edge[2]
            print("%d -- %d == %d" % (edge[0], edge[1], edge[2]))
        print("Minimum Spanning Tree" , minimumCost)
        return result

# class SpannigTree(NetGraph):

#     def __init__(self, Graph):
#         super().__init__(Graph.nodes, Graph.edges)
#         self.iselegible = True
#         self.edgesUtil  = []
        
        


class RemoteHost:
    @staticmethod
    def _run_on_rest(self, url, method, body = None, verbose = False):
        h = httplib2.Http()
        h.add_credentials(self.user_name, self.password)
        if body != None:
            resp, content = h.request(url, method, body, headers=self.headers)
        else:
            resp, content = h.request(url, method , headers=self.headers)
        result = resp['status']
        if (result == '200' or '201'):
            if verbose == True:
                print('Done.')
            return '0',content, resp
        else:
            if verbose == True:
                print('Error!')
            return '1', content, resp
            
        

    def __init__(self):
        self.baseurl = ''
        self.user_name = ''
        self.password = ''
        self.baseurl = ''
        self.headers = {'content-type': 'application/xml','accept':'application/xml'}
        self.sgw = GateWay()
        self.d_pgw = GateWay()
        self.flows = {}
        self.verbose = True
        self.stp = None
        
        
        
        with open('controller.txt') as controller_file:
            data = json.load(controller_file)
            ip = data['ip']
            port = data['port']
            username = data['username']
            password = data['password']
            self.user_name = username
            self.password = password
            self.baseurl = 'http://'+ip+':'+port
            controller_file.close()
        self.nodes, self.links  = self.get_topo(verbose = self.verbose)
        
        with open('gateways.txt') as gateways_file:
            data = json.load(gateways_file)
            
            
            self.d_pgw = GateWay(name = data['default pgw']['name'],tueip = data['default pgw']['tueip'],
                                 ofname=self.nodes[data['default pgw']['name']]['name'][0],
                                 ovsdbname=self.nodes[data['default pgw']['name']]['name'][1],
                                 mac = data['default pgw']['mac'], services = data['default pgw']['in_services'] )

            self.sgw = GateWay(name = data['sgw']['name'],tueip = data['sgw']['tueip'],
                                             ofname=self.nodes[data['sgw']['name']]['name'][0],
                                             ovsdbname=self.nodes[data['sgw']['name']]['name'][1],
                                             mac = data['sgw']['mac'], services = data['sgw']['in_services'] )
            gateways_file.close()
                
#             for pgw in data['pgws']:
#                 self.pgws[pgw['name']] = GateWay(name = pgw['name'],tueip = pgw['tueip'],
#                                                  ofname=self.nodes[pgw['name']]['name'][0],
#                                                  ovsdbname=self.nodes[pgw['name']]['name'][1],
#                                                  mac = pgw['mac'], services = pgw['in_services'] )
        if self.verbose == True:
            print('checking topology')

        if  self.d_pgw.name in self.nodes:
            if self.verbose == True:
                print('default pgw %s is connected' % self.d_pgw.name)
            
        else:
            if self.verbose == True:
                print('default pgw %s not connected' % self.d_pgw.name)
            return
      
        if  self.sgw.name in self.nodes:
            if self.verbose == True:
                print('sgw %s is connected' % self.sgw.name)
        else:
            if self.verbose == True:
                print('sgw %s not connected' % self.sgw.name)
            return

        
        
        
        if self.verbose == True:
            print('flushing flows on switches')

        
        for sw in self.nodes:
            ret, content, resp = self.flush_flows(self.nodes[sw]['name'][0])
            if ret == 0 :
                if self.verbose == True:
                    print('flows flushed')
            else:
                if self.verbose == True:
                    print('there was an error')

                    
        self.stp =self.makestp()
        
        print('end of initialization')
        #self.reconciliation()
        
                
               
        
        
    def getParentObjectNode(self, node, parent_tag):
        while node.parentNode:
            node = node.parentNode
            if node.nodeName == parent_tag:
                return node
            
    def alterElement(self, parent, attribute, newValue):
        found = False
 
        for child in [child for child  in parent.childNodes 
                    if child.nodeType != DOM.Element.TEXT_NODE]:
    
            if child.tagName == attribute:
      
                child.firstChild.data = newValue
                return True
            else:
      
              found = self.alterElement(child, attribute, newValue)
            if found:
                break

        
    def get_topo(self, verbose = True ):
        if verbose == True:
            print('start of topology discovery')
        url = self.baseurl+"/restconf/operational/network-topology:network-topology"
        method = 'GET'
        ret, content, resp = self._run_on_rest(self,url,method)
        if ret == '1':
            print('Topology not found')
            return resp
        else:
            dom = xml.dom.minidom.parseString(content.decode('utf-8'))
            nodeslist = dom.getElementsByTagName('node')
            nodes = {}
            
            for node in nodeslist:
                
                _node = {'name':[],'port':{}}
                node_id_list = node.getElementsByTagName('node-id')
                for node_id in node_id_list:
           
                    if 'openflow' in node_id.firstChild.nodeValue:
                        _node['name'].append(node_id.firstChild.nodeValue)
                        if verbose == True:
                            print('   '+node_id.firstChild.nodeValue)                    
                        portlist = node.getElementsByTagName('termination-point')
                        _port = {}
                        for port in portlist:
                            tplist = port.getElementsByTagName('tp-id')
                            for tp in tplist:
                                if 'LOCAL' not in tp.childNodes[0].nodeValue :
                                    tpnumber = tp.childNodes[0].nodeValue.split(':')[-1]
                                    _port[tpnumber] = {tp.childNodes[0].nodeValue: {'txbyte':self.query_port_statistics(tp.childNodes[0].nodeValue),'port_prio':1}} 
                                    if verbose == True:
                                        print('       '+tp.firstChild.nodeValue)
                        _node['port']= _port
                        for nd in nodeslist:
                            nd_id_list = nd.getElementsByTagName('node-id')
                            for nd_id in nd_id_list:
                                if 'sw' in nd_id.firstChild.nodeValue and 'sw'+node_id.firstChild.nodeValue.split(':')[1] == nd_id.firstChild.nodeValue.split('/')[-1]:
                                    _node['name'].append(nd_id.firstChild.nodeValue)
                                    if verbose == True:
                                        print('   '+nd_id.firstChild.nodeValue)
                                    plist = nd.getElementsByTagName('termination-point')
                                    for p in plist:
                                        pidlist = p.getElementsByTagName('tp-id')
                                        pofnumber =  p.getElementsByTagName('ofport')[0].childNodes[0].nodeValue
                                        for pid in pidlist:
                                            if nd_id.firstChild.nodeValue.split('/')[-1] != pid.childNodes[0].nodeValue :
                                                _port[pofnumber][pid.childNodes[0].nodeValue] = {'txbyte': 0,'port_prio':0}
                                                if verbose == True:
                                                    print('       '+pid.childNodes[0].nodeValue)
                        nodes['sw'+node_id.firstChild.nodeValue.split(':')[1]] = _node

#                 print(nodes)

#             if verbose == True:
#                 print("%d node:" % len(nodes))
#             nodeslist = dom.getElementsByTagName('node')
#             node_port_map = {}
#             for node in nodeslist:
#                 nid = node.getElementsByTagName('node-id')
#                 for n in nid:
#                     if 'openflow' in n.firstChild.nodeValue :#or 'sw' in n.firstChild.nodeValue :
#                         #if 'openflow' or 'sw' in node
#                         if verbose == True:
#                             print('   '+n.firstChild.nodeValue) 
#                         portlist = node.getElementsByTagName('termination-point')
#                         ports = []
#                         for port in portlist:
#                             tplist = port.getElementsByTagName('tp-id')
#                             for tp in tplist: 
#                                 if 'LOCAL' not in tp.childNodes[0].nodeValue :
#                                     ports.append(tp.childNodes[0].nodeValue)
#                                     if verbose == True:
#                                         print('       '+tp.firstChild.nodeValue)
#                         node_port_map[n.firstChild.nodeValue] = {'ports':ports}
            linklist = dom.getElementsByTagName('link')
            
            links = []
            for link in linklist:
                src = link.childNodes[1]
                src = src.getElementsByTagName('source-tp')[0]
                src = src.childNodes[0].nodeValue
                des = link.childNodes[2]
                des = des.getElementsByTagName('dest-tp')[0]
                des = des.childNodes[0].nodeValue
               # print('src and des=',src,des)
               # print('links is:',links)
                if len(links) == 0:
                    
                    links.append([src,des])
                    
                   # print('list was empty')
                else:
                    isin = False
                    for lk in links:
                       # print('lk is',lk[0],lk[1])
                        if ((lk[0] == src and lk[1] == des) or (lk[1] == src and lk[0] == des)):
                           # print('it was in list')
                            isin = True
                            break
                    if isin == False:
                        #print('it wasnt in list')
                        links.append([src,des])
                        
                        #print('links is:',links)
                #links.append((src.replace(":","."),des.replace(":",".")))
        if verbose == True:
            print('%d node ' % len(nodes))
            print('%d links ' % len(links))
            print('------------\n')
            print('nodes are:\n',nodes)
            print('------------\n')
            print('links are:\n',links)
            print('------------\n')
            print('end of topology discovery')

        return nodes, links
        
    def makestp(self):
        g = Stp(len(self.nodes))
        for link in self.links:
            src = link[0].split(':')[1]
            det = link[1].split(':')[1]
            weight = self.nodes['sw'+link[0].split(':')[1]]['port'][link[0].split(':')[2]][link[0]]['port_prio']
            g.addedge(int(src)-1, int(det)-1,weight)
        stp = g.KruskalMST()
        _stp = []
        for lk in self.links:
            for l in stp:
                if (int(lk[0].split(':')[1]) == int(l[0]) and int(lk[1].split(':')[1]) == int(l[1]) ) or (int(lk[0].split(':')[1]) == int(l[1]) and int(lk[1].split(':')[1]) == int(l[0]) ):
                    _stp.append(lk)
                    break
        if self.verbose == True:    
            print('stp links are: ',_stp)
        return _stp
    ################################################work here########################################
    def reconciliation(self):
        #take hot link out of _list
        links = self.links
        #print(links)
        
            
        for link in links:
            if  (self.d_pgw.ofname in link[0]) or (self.d_pgw.ofname in link[1]):
                links.remove(link)
            continue
            for sgw in self.sgws:
                if (self.sgws[sgw].ofname in link[0]) or (self.sgws[sgw].ofname in link[1]):
                    links.remove(link)
                    break
            continue
#             for pgw in self.pgws:
#                 if (self.pgws[pgw].ofname in link[0]) or (self.pgws[pgw].ofname in link[1]):
#                     links.remove(link)
#                     break
#             continue
            
        print(links)
        return

    def query_port_current_speed(self,portname):
        node = 'openflow:'+portname.split(':')[1]
        url = self.baseurl+'/restconf/operational/opendaylight-inventory:nodes/node/'+node+'/node-connector/'+portname
        ret, content, resp = self._run_on_rest(self,url, 'GET')
        dom = xml.dom.minidom.parseString(content.decode('utf-8'))
        pretty_xml_as_string = dom.toprettyxml()
        cs = dom.getElementsByTagName('current-speed')[0].firstChild.nodeValue
#         for byte in list_byte :
#             byte = byte.getElementsByTagName('transmitted')[0].firstChild.nodeValue

        return int(cs)

    def query_port_statistics(self,portname):
        node = 'openflow:'+portname.split(':')[1]
        url = self.baseurl+'/restconf/operational/opendaylight-inventory:nodes/node/'+node+'/node-connector/'+portname
        ret, content, resp = self._run_on_rest(self,url, 'GET')
        dom = xml.dom.minidom.parseString(content.decode('utf-8'))
        pretty_xml_as_string = dom.toprettyxml()
        list_byte = dom.getElementsByTagName('bytes')
        for byte in list_byte :
            byte = byte.getElementsByTagName('transmitted')[0].firstChild.nodeValue

        return int(byte)

    def create_queue(self,ovsdb_name , queue_name, queue_max_rate):
        sw = ovsdb_name.replace("/","%2F") 
        sw_host,sw_client = sw.split('%2Fbridge') #find ovs host
        # create queue
        queue_id = queue_name
        max_rate = queue_max_rate
        url = self.baseurl+'/restconf/config/network-topology:network-topology/topology/ovsdb:1/node/'+sw_host+'/ovsdb:queues/'+queue_id
        queue = xml.dom.minidom.parse("queue.xml")
        ret = self.alterElement(queue, "queue-id",queue_id)
        ret = self.alterElement(queue, "queue-other-config-value",max_rate)
        ret, content, resp = self._run_on_rest(self,url, 'PUT', queue.toprettyxml())
        print(resp)

    def query_queue(self,ovsdb_name, queue_name):
        queue_id = queue_name
        sw = ovsdb_name
        sw = sw.replace("/","%2F") 
        sw_host,sw_client = sw.split('%2Fbridge') #find ovs host
        url = self.baseurl+'/restconf/operational/network-topology:network-topology/topology/ovsdb:1/node/'+sw_host+'/ovsdb:queues/'+queue_id
        ret, content, resp = self._run_on_rest(self,url, 'GET')
        dom = xml.dom.minidom.parseString(content.decode('utf-8'))
        pretty_xml_as_string = dom.toprettyxml()
        q_ref = dom.getElementsByTagName('queues-external-id-value')[0].childNodes[0].nodeValue
        return q_ref

    def create_qos(self, ovsdb_name, qos_name, queue_name, max_rate):
        queue_id = queue_name
        sw = ovsdb_name
        sw = sw.replace("/","%2F")
        sw_host,sw_client = sw.split('%2Fbridge') #find ovs host
        queue_ref = self.query_queue(ovsdb_name, queue_name)
        with open('qos.json') as json_file:
            qos = json.load(json_file)
            for entry in qos["ovsdb:qos-entries"]:
                entry["qos-id"] = qos_name
                for other_conf in entry["qos-other-config"]:
                    other_conf["other-config-value"] = max_rate
                for queue_list in entry["queue-list"]:
                    queue_list["queue-ref"] = queue_ref
        url = self.baseurl+'/restconf/config/network-topology:network-topology/topology/ovsdb:1/node/'+sw_host+'/ovsdb:qos-entries/'+qos_name
        self.headers['content-type'] = 'application/json'
        ret, content, resp = self._run_on_rest(self,url, 'PUT',  json.dumps(qos))
        self.headers['content-type'] = 'application/xml'
        print(resp)
    
    def query_qos(self,ovsdb_name, qos_name):
        
        qos_id = qos_name
        sw = ovsdb_name
        sw = sw.replace("/","%2F") 
        sw_host,sw_client = sw.split('%2Fbridge') #find ovs host
        url = self.baseurl+'/restconf/operational/network-topology:network-topology/topology/ovsdb:1/node/'+sw_host+'/ovsdb:qos-entries/'+qos_id
        ret, content, resp = self._run_on_rest(self,url, 'GET')
        dom = xml.dom.minidom.parseString(content.decode('utf-8'))
        qos_uuid = dom.getElementsByTagName('qos-uuid')[0].childNodes[0].nodeValue   
        return qos_uuid

    def attach_qos_port(self, ovsdb_name, port_name, qos_name, queue_name):
        qos_id = qos_name
        sw = ovsdb_name
        sw = sw.replace("/","%2F")
        qos_uuid = self.query_qos(ovsdb_name, qos_name)
        # Add QoS to a tunnel Port
        with open('port-qos.json') as json_file:
            port_qos = json.load(json_file)
            for entry in port_qos["network-topology:termination-point"]:
                entry['qos'] = qos_uuid
                entry['ovsdb:name'] = port_name
                entry['tp-id'] = port_name
        url = self.baseurl+'/restconf/config/network-topology:network-topology/topology/ovsdb:1/node/'+sw+'/termination-point/'+port_name
        print(url)
        print(json.dumps(port_qos))
        self.headers['content-type'] = 'application/json'
        ret, content, resp = self._run_on_rest(self,url, 'PUT',  json.dumps(port_qos))
        self.headers['content-type'] = 'application/xml'
        print(ret)
        print("#################")
        print(resp)
        print("#################")

        return  content, resp
        
    def add_qos_port(self, ovsdb_name, port_name, qos_name, queue_name, qos_max_rate, queue_max_rate):
    
        qos_id = qos_name
        sw = ovsdb_name
        sw = sw.replace("/","%2F") 
        # Add QoS to a tunnel Port
        qos_port = xml.dom.minidom.parse("port-qos.xml")
        ret = create_queue(sw_number, queue_name, queue_max_rate)
        ret = create_qos(sw_number, qos_name, queue_name, qos_max_rate)
        q_uuid = query_qos(sw_number, queue_name)
        ret = self.alterElement(qos, "qos",qos_uuid)
        url = self.baseurl+'/restconf/config/network-topology:network-topology/topology/ovsdb:1/node/'+sw+'/termination-point/'+port_name
        ret, content, resp = self._run_on_rest(url, 'PUT', qos_port.toprettyxml())
        print(resp)
        
    def query_sw(self, ovsdb_name):  
        # Query the OVSDB Node
        
        sw = ovsdb_name
        sw = sw.replace("/","%2F") 
        sw_host,sw_client = sw.split('%2Fbridge') #find ovs host
        url = self.baseurl+'/restconf/operational/network-topology:network-topology/topology/ovsdb:1/node/'+sw_host
        ret, content, resp = self._run_on_rest(url, 'GET')
        dom = xml.dom.minidom.parseString(content.decode('utf-8'))
        print(dom.toprettyxml())
    
    def flush_flows(self, node):
        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0'

        ret, content, resp = self._run_on_rest(self,url, 'DELETE')
        return ret, content, resp
    
    
    def add_gt_ul__flow(self, node = 'openflow:1', input_port ='1', tueid ='2',tueip = '192.168.60.4', tuport='10'
                      ,priority = '1000',flow_id = '1000', flow_name = ''):
        tueip = tueip.split('.')
        tueip =(int(tueip[0]) << 24) + (int(tueip[1]) << 16)+(int(tueip[2]) << 8) + int(tueip[3])    
        
                          
        flow = xml.dom.minidom.parse("gto-def-qos-ul.xml") # or xml.dom.minidom.parseString(xml_string)

        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.getElementsByTagName('match')[0], 'in-port', input_port)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-ipv4-dst')[0],'nx-reg-load') 
                           ,'value', tueip)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-id')[0],'nx-reg-load') 
                           ,'value', tueid)

        ret = self.alterElement(flow.childNodes[0], "output-node-connector", tuport)

        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id

        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        return content , resp
    
    def add_gt_ul_flow(self, node = 'openflow:1', input_port ='1', tueid ='2',tueip = '192.168.60.4', tuport='10'
                      ,priority = '1000',flow_id = '1000', flow_name = ''):
        tueip = tueip.split('.')
        tueip =(int(tueip[0]) << 24) + (int(tueip[1]) << 16)+(int(tueip[2]) << 8) + int(tueip[3])    
        
                          
        flow = xml.dom.minidom.parse("gtp-def-UL.xml") # or xml.dom.minidom.parseString(xml_string)

        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.getElementsByTagName('match')[0], 'in-port', input_port)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-ipv4-dst')[0],'nx-reg-load') 
                           ,'value', tueip)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-id')[0],'nx-reg-load') 
                           ,'value', tueid)

        ret = self.alterElement(flow.childNodes[0], "output-node-connector", tuport)

        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id

        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        return content , resp
    

    def add_gt_dl_flow(self, node = 'openflow:1', flow_id = '1000', priority = '101', eth_add = '00:00:00:00:00:06'
                       , flow_name = '', tueid ='2', out_port = '1'):
        flow = xml.dom.minidom.parse("gtp-DL.xml") # or xml.dom.minidom.parseString(xml_string)         
        
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.getElementsByTagName('tunnel')[0], 'tunnel-id', tueid)
        ins = flow.getElementsByTagName('instruction')[0]
        eth_des = ins.getElementsByTagName('ethernet-destination')[0]
        ret = self.alterElement(eth_des, "address",eth_add)
        ret = self.alterElement(flow.getElementsByTagName('output-action')[0], 'output-node-connector', out_port)
        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id
        
        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        return content , resp 

    def add_gt__ul_flow(self, node = 'openflow:1', input_port ='1', tueid ='2',tueip = '192.168.60.4', tuport='10'
                      ,priority = '1000',flow_id = '1000',des_ip = '0.0.0.0/0', flow_name = ''):
        tueip = tueip.split('.')
        tueip =(int(tueip[0]) << 24) + (int(tueip[1]) << 16)+(int(tueip[2]) << 8) + int(tueip[3])    
        
                          
        flow = xml.dom.minidom.parse("gtp-UL.xml") # or xml.dom.minidom.parseString(xml_string)

        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.childNodes[0], "ipv4-destination", des_ip)
        ret = self.alterElement(flow.getElementsByTagName('match')[0], 'in-port', input_port)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-ipv4-dst')[0],'nx-reg-load') 
                           ,'value', tueip)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-id')[0],'nx-reg-load') 
                           ,'value', tueid)

        ret = self.alterElement(flow.childNodes[0], "output-node-connector", tuport)

        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id
        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        return content , resp
    
    
    def add_gtp_up(self, node = '', tueid ='',tueip = '', tuport=''
                      ,priority = '',flow_id = '', flow_name = '', src_ip = '', des_ip = ''):
        tueip = tueip.split('.')
        tueip =(int(tueip[0]) << 24) + (int(tueip[1]) << 16)+(int(tueip[2]) << 8) + int(tueip[3])    
        
                          
        flow = xml.dom.minidom.parse("1.xml") # or xml.dom.minidom.parseString(xml_string)

        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.childNodes[0], "ipv4-source", src_ip)
        ret = self.alterElement(flow.childNodes[0], "ipv4-destination", des_ip)
        

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-ipv4-dst')[0],'nx-reg-load') 
                           ,'value', tueip)

        ret = self.alterElement(self.getParentObjectNode(flow.getElementsByTagName('nx-tun-id')[0],'nx-reg-load') 
                           ,'value', tueid)

        ret = self.alterElement(flow.childNodes[0], "output-node-connector", tuport)

        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id

        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        
        return content , resp

    def add_gtp_down(self, node = '', flow_id = '', priority = '', eth_add = ''
                       , flow_name = '', tueid ='', out_port = ''):
        flow = xml.dom.minidom.parse("2.xml") # or xml.dom.minidom.parseString(xml_string)         
        
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.getElementsByTagName('tunnel')[0], 'tunnel-id', tueid)
        ins = flow.getElementsByTagName('instruction')[0]
        eth_des = ins.getElementsByTagName('ethernet-destination')[0]
        ret = self.alterElement(eth_des, "address",eth_add)
        ret = self.alterElement(flow.getElementsByTagName('output-action')[0], 'output-node-connector', out_port)
        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id
        
        
        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        return content , resp 
    
    def gtp_routing(self, node = '', flow_id = '', priority = '', flow_name = '',
                    out_port = '', src_ip = '', des_ip = ''):
        flow = xml.dom.minidom.parse("3.xml") # or xml.dom.minidom.parseString(xml_string)         
        
        ret = self.alterElement(flow.childNodes[0], "id", flow_id)
        ret = self.alterElement(flow.childNodes[0], "flow-name", flow_name)
        ret = self.alterElement(flow.childNodes[0], "priority", priority)
        ret = self.alterElement(flow.childNodes[0], "ipv4-source", src_ip)
        ret = self.alterElement(flow.childNodes[0], "ipv4-destination", des_ip)
    
        ins = flow.getElementsByTagName('instruction')[0]
        ret = self.alterElement(flow.getElementsByTagName('output-action')[0], 'output-node-connector', out_port)
        url = self.baseurl+'/restconf/config/opendaylight-inventory:nodes/node/'+node+'/table/0/flow/'+flow_id
        
        
        ret, content, resp = self._run_on_rest(self,url, 'PUT', flow.toprettyxml())
        
        return content , resp 
    
    
    
    
    
    

controller = RemoteHost()

portmonitor = myThread(controller,1, "port_monitor")

   
portmonitor.start()


# for node in controller.nodes:
#     ports = controller.nodes[node]['port']
#     for port in ports:
#         for _port in port:
#             pt = port[_port][0]
# cs = controller.query_port_current_speed('openflow:5:2')

# byte = controller.query_port_statistics('openflow:5:2')
# for i in range(5):
#     time.sleep(10)
#     new_byte = controller.query_port_statistics('openflow:5:2')
#     r =( int(new_byte) - int(byte)) 
#     byte = new_byte 
#     r = r / 10
#     if int(cs) *0.8 >= r:   
#         print('link is not utilized')


def exit():
    print('exiting')
    myThread.exitFlag = 1
    portmonitor.join()
    print('main exiting') 
    

def defaultbearer(args):
    with open('clients.json') as client_file:
        clients = json.load(client_file)
        client = clients[args]
        client_file.close()
  
    current = 'openflow:5'
    last = controller.d_pgw.ofname 
    stp = controller.stp[:]
    path = []
    path_links = []
    while current not in last: 
        for idx,link in enumerate(stp):
            if current in link[0]:

                stp.pop(idx)
                path.append(link[0])
                path_links.append(link)
                current = link[1].split(':')[0]+':'+link[1].split(':')[1]
                if current in last:
                    path.append(link[1])


                break

            elif current in link[1]:
                stp.pop(idx)
                path.append(link[1])
                path_links.append([link[1],link[0]])
                current = link[0].split(':')[0]+':'+link[0].split(':')[1]
                if current in last:
                    path.append(link[0])

                break
    print('chosen path is:')
    path_txt = ''
    for sw in path:
        name = sw.split(':')[1]
        path_txt+= name+'<-->'
    
    print(path_txt[:-4])
    print(path_links)
    
    flow_id = int(args[-1])*100
    for idx,link in enumerate(path_links):
        node = link[0].split(':')[0]+':'+link[0].split(':')[1]
        port = link[0].split(':')[-1]
        if node == controller.sgw.ofname:
            print('set gtp uplink side flow %s for host %s on node %s'  %(flow_id,args[-1] ,node))
            content,resp=controller.add_gtp_up(node = node, tueid =client['tueid'] ,tueip = '192.168.60.4', tuport='10'
                                              ,priority = '101',flow_id = str(flow_id), flow_name = 'GTP-UL-CAP', src_ip = client['ip'], des_ip = '10.0.0.6/32')
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('GTP-UL-CAP',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
        elif idx == 0:
            print('publishing uplink flow %s on switch %s for host %s' %(flow_id,node, args[-1]))

            content,resp=controller.gtp_routing(node = node, flow_id = str(flow_id), priority = '100', flow_name = 'UP_ROUTING_FLOW', 
                                                out_port = port, src_ip = client['ip'], des_ip = '10.0.0.6/32')
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('UP_ROUTING_FLOW',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
            
            print('publishing downlink flow %s on switch %s for host %s' %(flow_id,node, args[-1]))
            
            content,resp=controller.gtp_routing(node = node, flow_id = str(flow_id), priority = '100', flow_name = 'DOWN_ROUTING_FLOW', 
                                                out_port = client['port'], src_ip = '10.0.0.6/32', des_ip = client['ip'])
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('DOWN_ROUTING_FLOW',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
        else:
            print('publishing uplink flow %s on switch %s for host %s' %(flow_id,node, args[-1]))

            content,resp=controller.gtp_routing(node = node, flow_id = str(flow_id), priority = '100', flow_name = 'UP_ROUTING_FLOW', 
                                                out_port = port, src_ip = client['ip'], des_ip = '10.0.0.6/32')
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('UP_ROUTING_FLOW',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
        
            
            
        
        
        node = link[1].split(':')[0]+':'+link[1].split(':')[1]
        port = link[1].split(':')[-1]
        if node == controller.d_pgw.ofname:
            print('set gtp downlink side %s flow for host %s on node %s'  %(flow_id,args[-1] ,node))
            content,resp=controller.add_gtp_up(node = node, tueid =client['tueid'] ,tueip = '192.168.60.3', tuport='10',
                                               priority = '101',flow_id = str(flow_id), flow_name = 'GTP-DL-CAP', src_ip = '10.0.0.6/32', des_ip = client['ip'])
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('GTP-DL-CAP',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')

 
            print('set gtp uplink side flow %s for host %s on node %s'  %(flow_id,args[-1] ,node))
            content,resp=controller.add_gtp_down(node = node, flow_id = str(flow_id), priority = '101', eth_add = '00:00:00:00:00:16',
                                                 flow_name = 'GTP-UL-DECAP', tueid =client['tueid'], out_port = '1')
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('GTP-DL-DECAP',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
        
        elif node == controller.sgw.ofname:
            print('set gtp downlink side flow %s for host %s on node %s'  %(flow_id,args[-1] ,node))
            content,resp=controller.add_gtp_down(node = node, flow_id = str(flow_id), priority = '101', eth_add = client['mac'],
                                                 flow_name = 'GTP-DL-DECAP', tueid =client['tueid'], out_port = port)
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('GTP-DL-DECAP',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')
            
        else:
            print('publishing downlink flow %s on switch %s for host %s' %(flow_id,node, args[-1]))

            content,resp=controller.gtp_routing(node = node, flow_id = str(flow_id), priority = '100', flow_name = 'DOWN_ROUTING_FLOW',
                                                out_port = port, src_ip = '10.0.0.6/32', des_ip = client['ip'])
            if resp['status'] != '200' and resp['status'] != '201':
                print("flow dosen't add")
                print(content)
            flow = Flow('DOWN_ROUTING_FLOW',node)
            controller.flows[flow_id]= flow
            flow_id+=1
            print('------------------------------')

        
        

            
            
            
            
        
        
            






        
        
            
       
              
            
        

while not myThread.exitFlag:
    
    while True:
        try:
            number1 = int(input('Number1: '))
            if number1 < 0 or number1 > 2:
                raise ValueError 
            break
        except ValueError:
            print("Invalid integer. The number must be in the range of 1-4. \n"
                  "1 for make default bearer, 2 for exit")
    if number1 == 1:
        exit()
    
    if number1 == 2 :
        with open('clients.json') as client_file:
            clients = json.load(client_file)
            client_file.close()
        while True:
            try:
                print('client name for add bearer form this list', *clients.keys(), sep='\n')
                cl = input('client: ')
                if cl  not in clients.keys() :
                    raise ValueError 
                break
            except ValueError:
                print("Invalid client name.")
        defaultbearer(cl)

        
 



    


        
        
        

if '-info' in sys.argv:
    nodes, node_port_map  = controller.get_topo()

if '-init' in sys.argv:
    controller = RemoteHost()
    with open('gateways.txt') as gateways_file:
        data = json.load(gateways_file)




if '-add_default_bearer' in sys.argv:
    max_rate = sys.argv[sys.argv.index('-add_default_bearer') + 1]
    for _sgw in controller.sgws:
        sgw = controller.sgws[_sgw]
        print('set qos to'+ str(int(max_rate)/1000000)+'mB')
        controller.create_queue(sgw.ovsdbname, "queue-1", max_rate)
        controller.create_qos(sgw.ovsdbname, 'qos-1', "queue-1", '1000000000')
        print('attaching queue to port')
        content,resp=controller.attach_qos_port(sgw.ovsdbname, 'tun1', 'qos-1', "queue-1")
        if resp['status'] != '200' and resp['status'] != '201':
            print("queue dosen't attached")
            print(content)
        else:
            print('queue attached\n')  
        print('------------------------------')

        print('set gtp uplink side flow for node '+sgw.ofname)
        content,resp=controller.add_gt_ul__flow(node = sgw.ofname, flow_name ="defbearer" , flow_id = '1000', priority = '101', input_port ='1',
                                               tueip = controller.d_pgw.tueip, tueid ='1', tuport='10')
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)
        print('------------------------------')




        print('set gtp downlink slide flow for node '+sgw.ofname)
        content,resp=controller.add_gt_dl_flow(node = sgw.ofname, flow_name ="defbearer" , flow_id = '1001', priority = '101', eth_add = sgw.mac,
                                               tueid ='1', out_port = sgw.services['test']['inport'])
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)
        print('------------------------------')

        print('set gtp uplink slide flow for node '+controller.d_pgw.ofname)
        content,resp=controller.add_gt_ul_flow(node = controller.d_pgw.ofname, flow_name ="defbearer" , flow_id = '1000', priority = '101',
                                               input_port ='1', tueip = sgw.tueip, tueid ='1', tuport='10')
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)
        print('------------------------------')


        print('set gtp downlink slide flow for node '+controller.d_pgw.ofname)    
        content,resp=controller.add_gt_dl_flow(node = controller.d_pgw.ofname, flow_name ="defbearer" , flow_id = '1001', priority = '101',
                                               eth_add = controller.d_pgw.mac, tueid ='1', out_port = controller.d_pgw.services['test']['inport'])
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)
        else:
            print('all flows creted')

if '-add_bearer' in sys.argv:
    pgw = sys.argv[sys.argv.index('-add_bearer') + 1]
    pgw = controller.pgws[pgw]
    service_name = sys.argv[sys.argv.index('-add_bearer') + 2]
   ################################################################ 
    max_rate = sys.argv[sys.argv.index('-add_bearer') + 3]
    for _sgw in controller.sgws:
        sgw = controller.sgws[_sgw]
        print('set qos to'+ str(int(max_rate)/1000000)+'mB')
        controller.create_queue(sgw.ovsdbname, "queue-2", max_rate)
        controller.create_qos(sgw.ovsdbname, 'qos-2', "queue-2", '1000000000')
        print('attaching queue to port')
        content,resp=controller.attach_qos_port(sgw.ovsdbname, 'tun1', 'qos-2', "queue-2")
        if resp['status'] != '200' and resp['status'] != '201':
            print("queue dosen't attached")
            print(content)
        else:
            print('queue attached\n')  
        print('------------------------------')     
   ############################################################### 

        print('set gtp uplink slide flow for node '+sgw.ofname)
        content,resp=controller.add_gt__ul_flow(node = sgw.ofname, flow_name ="bearer_"+service_name , flow_id = '2000', priority = '102',
                                                input_port ='1', tueip = pgw.tueip, tueid ='2', tuport='10', des_ip = pgw.services[service_name]['inip'])
        print(content)
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)

        print('set gtp downlink slide flow for node '+sgw.ofname)
        content,resp=controller.add_gt_dl_flow(node = sgw.ofname, flow_name ="bearer_"+service_name , flow_id = '2001', priority = '102',
                                               eth_add = sgw.mac, tueid ='2', out_port = sgw.services['test']['inport'])
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)

        print('set gtp uplink slide flow for node '+pgw.ofname)
        content,resp=controller.add_gt_ul_flow(node = pgw.ofname, flow_name ="bearer_"+service_name , flow_id = '2000', priority = '102',
                                               input_port ='1', tueip = sgw.tueip, tueid ='2', tuport='10')
        if resp['status'] != '200' and resp['status'] != '201':
            print("flow dosen't add")
            print(content)

        print('set gtp downlink slide flow for node '+pgw.ofname)    
        content,resp=controller.add_gt_dl_flow(node = pgw.ofname, flow_name ="bearer_"+service_name , flow_id = '2001', priority = '102',
                                               eth_add = pgw.mac, tueid ='2', out_port = pgw.services['test']['inport'])
        if resp['status'] != '200' and resp['status'] != '201':

            print("flow dosen't add")
            print(content)


        

if '-stats' in sys.argv:
    with open('info.txt', 'r') as info_file:
        for line in info_file:
            tokens = line.split()
            if tokens[0] in ip_to_rhost_map.keys():
                ip_to_rhost_map[tokens[0]].install_script('read_stats.sh',
                                                          COLLECTOR_IP, COLLECTOR_PORT, TIME_INTERVAL, tokens[2], tokens[1])