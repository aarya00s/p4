import socket
import struct
import threading
import time
import sys
import json
from router import RouterClass
ip_add = ['224.1.1.1','224.1.1.2']
ip_port = 33007
MULTICAST_TTL = 1
node_port = 33008
routing_port = 33009
in_port = 33010
in_id = '224.1.1.5'
class Node:
    nodelistt = {}
    router_id = ""
    routing = {}
    disc = {}
    def __init__(self, host, port, hostname, networkname):
        self.host = host
        self.hostname = hostname
        self.port = port
        self.ip_add = ip_add[int(networkname) - 1]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.unicastsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.routingsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.gatewaysock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
        
        def setrouter_id(self, name):
            self.router_id = name
        
    def handleRootFailure(self):
        minNode = 1000000
        for addr in list(self.disc):
            nodeNumber = addr[4:]
            if int(nodeNumber) < minNode:
                minNode = int(nodeNumber)
                
        newRoot = "node" + str(minNode)
        if self.router_id == newRoot:
            self.setrouter_id("root")
            print("node", minNode, " is new root")
        
    def handleRouting(self):
        self.routingsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.routingsock.bind(('', routing_port))
        mreq = struct.pack("4sl", socket.inet_aton(self.ip_add), socket.INADDR_ANY)
        self.routingsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, addr = self.routingsock.recvfrom(10240)
            broadcastDBJson = data.decode("utf-8")
            db = json.loads(broadcastDBJson)
            for key in db:    #Take every key in the incoming db
                #print("AFTER PARSING:: ", db[key]);
                currentValue = self.routing[key]
                newValue = db[key]
                newValue[1] = newValue[1]+1   #Increment hop
                
                if key == self.router_id:
                    continue                 # This is out own key, do nothing
                if key in self.routing:    # If key is present in routing
                    
                    if currentValue[1] > newValue[1]:     # If current hop count is greater than received hop count, replace with new
                        self.routing[key] = newValue 
                        #print("routing after entry::", self.routing)
                    else:                        # key is not present in DB, so make a new entry
                        self.routing[key] = newValue
            
    def broadcastDatabase(self):
        while(True):
            #Create the routing database
            for node in self.disc:
                values = self.disc[node]
                self.routing[node] = values
                print("Routing DB new entry::: ", self.routing)
            #print("Routing DB: ", self.routing)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
            dict_json = json.dumps(self.routing)
            #print("!!!!!!!!!!!!!", dict_json)
            self.sock.sendto(dict_json.encode('utf-8'), (self.ip_add, routing_port))
            #print(self.router_id, " has broadcasted its database...")
            time.sleep(30)


    def handleDiscovery(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip_add, ip_port))

        mreq = struct.pack("4sl", socket.inet_aton(self.ip_add), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, addr = self.sock.recvfrom(10240)
            router_id = data.decode("utf-8")
            #print(time.time(), "::Received message in handleDiscovery: ", router_id, " from IP: ", addr)
            self.nodelistt[router_id] = time.time()
            #print("handleDiscovery IP Address List: ",self.nodelistt)
            if addr not in list(self.nodelistt):
                self.disc[router_id] = list()
                values = [addr, 1]
                self.disc[router_id].extend(values)
                
            detail = self.disc[router_id]

    def generateSensorData(self):
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        sensorobj = RouterClass(host,node_port)
        while True:
            sensorobj.getData()

    def listenToSensor(self):
        self.unicastsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
        # This port will listen to unicast sensor communication
        self.unicastsock.bind((self.hostname,node_port))

        while True:
            data, _ = self.unicastsock.recvfrom(10240)
            if self.router_id == "root":
                self.detectFire(data)

    def detectFire(self, data):
        #print("SENSOR DATA RECIEVED")
        sensorJson = data.decode("utf-8")
        if (sensorJson[:14] == "Recieved Image"):
            if( sensorJson.find('FIRE') != -1 ):
                # Alert SOS across networks
                msg = "################### SOS ####################### \n ----------   Fire ALERT!!!!!  ----------- \n ################### SOS #######################"
                self.gatewaysock.sendto(msg.encode("utf-8"), (in_id, in_port))
        else:
            print(sensorJson)

    # This handles communication across networks using a gateway
    def gatewayListen(self):
        if self.router_id == "root":

            self.gatewaysock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.gatewaysock.bind((in_id, in_port))

            mreq = struct.pack("4sl", socket.inet_aton(in_id), socket.INADDR_ANY)
            self.gatewaysock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while True:
                data, _ = self.gatewaysock.recvfrom(10240)
                print(data.decode('utf-8'))    

    def start(self, router_id):
        self.setrouter_id(str(sys.argv[1]))
        
        gatewayThread = threading.Thread(target=self.gatewayListen)
        gatewayThread.setDaemon(True)
        gatewayThread.start()

        discoveryThread = threading.Thread(target=self.handleDiscovery)
        discoveryThread.setDaemon(True)
        discoveryThread.start()
        
        SensorThread = threading.Thread(target=self.listenToSensor)
        SensorThread.setDaemon(True)
        SensorThread.start()
            
        checkNodesThread = threading.Thread(target=self.checkNodes)
        checkNodesThread.setDaemon(True)
        checkNodesThread.start()
        
        broadcastNodeThread = threading.Thread(target=self.broadcastNode)
        broadcastNodeThread.setDaemon(True)
        broadcastNodeThread.start()
        
        time.sleep(15)
        
        routingThread = threading.Thread(target=self.handleRouting)
        routingThread.setDaemon(True)
        routingThread.start()
        
        broadcastDatabaseThread = threading.Thread(target=self.broadcastDatabase)
        broadcastDatabaseThread.setDaemon(True)
        broadcastDatabaseThread.start()

        getDataThread = threading.Thread(target=self.generateSensorData)
        getDataThread.setDaemon(True)
        getDataThread.start()

def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    networkname = sys.argv[2].replace('network', '')
    
    if(not networkname.isdigit() or not int(networkname) in (1,2)):
        print("Please enter a valid network name")
        exit(1)

    node = Node(host, ip_port, hostname, networkname)
    
    node.start(str(sys.argv[1]))

    while True:
        pass
    
if __name__ == '__main__':
    main()
    
