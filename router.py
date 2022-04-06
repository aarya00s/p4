
import socket
import random
import time
NODE_PORT = 33008
class RouterClass():
    def __init__(self, host, port):
        #define socket 
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    def getData(self):
            # Send data from packet drone_router to identify if its a poacher or not
            print("SENDING DATA FROM drone_router")
            host = socket.gethostbyname(socket.gethostname())
            drone_router = RouterClass(host, NODE_PORT)
            aqi_list = ['30aqi:GOOD','FIRE','60aqi:Moderate','90aqi:Moderate ','140aqi:Unhealthy','190aqi:Unhealthy','240aqi:Warning','280aqi:Warning','320aqi:Hazard','360aqi:Hazard','400aqi:Hazard','50aqi:GOOD','40aqi:GOOD','10aqi:GOOD','20aqi:GOOD']
            aqi = aqi_list[random.randint(0,14)]
            packet = f'{"Recieved api from drone : "}{aqi}'
            data_encode = packet.encode("utf-8")
            print("Sending data to the router")
            drone_router.sock.sendto(data_encode, (host,NODE_PORT))
            # Coordinates of router 
            lat = round(random.uniform(50.1, 59.9), 5)
            long = round(random.uniform(3.4, 6.2), 5)
            location = f'{"lat : "}{lat}{" long_recived  : "}{long}'
            data_encode = location.encode("utf-8")
            print("Sending data")
            drone_router.sock.sendto(data_encode, (host,NODE_PORT))
            alert_val = f'{"Alert Level:"}{random.randint(10, 100)}'
            data_encode = alert_val.encode("utf-8")
            print("Sending Alert Level")
            drone_router.sock.sendto(data_encode, (host, NODE_PORT))

def main():
    print("router")

if __name__ == '_main_':
    main()          