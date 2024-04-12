import socket
import threading
import struct
import time
import os
import netifaces as ni
import services

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Multicast configuration
MULTICAST_GROUP = '224.1.1.1'   
MULTICAST_PORT = 5007
MULTICAST_TTL = 2

NAME = os.environ.get("NAME")
RESEND_ATTEMP = 3
ALONE_STATUS = True


def categorizeData(data):
    return (data.split(':')[0], data.split(':')[1])

def getStateFromLocal():
    try:
        # Try to read timestamp from state.txt
        with open("state.txt", "r") as file:
            timestamp = file.read().strip()
            # print("Timestamp from state.txt:", timestamp)
    except FileNotFoundError:
        # If state.txt doesn't exist, create it with current timestamp
        timestamp = str(time.time())
        with open("state.txt", "w") as file:
            file.write(timestamp)
            print("Created state.txt with current timestamp.")
    return timestamp
        

def send_ts_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    
    ts = getStateFromLocal()
    message = f'SEND_STATE:{ts}'
    
    while True:
        sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))

        # Set a timeout for receiving acknowledgment
        sock.settimeout(3)  # 3 seconds timeout
        try:
            acknowledgment, _ = sock.recvfrom(1024)
            print(f"ACK: {acknowledgment.decode()}")
            break  # Exit the loop if acknowledgment received
        except socket.timeout:
            print("Resending the TS.")
            continue  # Continue to next iteration without waiting
        
        
        
        
        
# Peer discovery and acknowledgment
def peer_communication():
    receiver_ip = services.get_ip_address()
    print("Local IP:", receiver_ip, end="\n")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, address = sock.recvfrom(10240)
        sender_ip, sender_port = address

        # Check if the sender IP matches the receiver IP
        if sender_ip == receiver_ip:
            # Ignore the message from itself
            continue
        type, message = categorizeData(data.decode()) 
        if type == "GREETING":
            print("GREETING as:", message)  
            acknowledgment_message = f"ACK from {NAME}'s notebook"
            sock.sendto(acknowledgment_message.encode(), address)
            
        elif type == "ACK":
            print("ACK as", sender_ip)
        elif type == "GET_STATE":
            print("GET_STATE as", message)
            send_ts_broadcast()
        elif type == "SEND_STATE":
            print("SEND_STATE", message)
            state_recieved_message = f"State recieved from {NAME}'s notebook"
            sock.sendto(state_recieved_message.encode(), address)
        else:
            print(data.decode())


# Peer broadcasting using multicast
def greeting_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

    message = f"GREETING: I'm {NAME}!"
    retry_count = 0
    while retry_count < RESEND_ATTEMP:  # Retry only twice
        sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
        print(f"Sent: {message}")

        # Set a timeout for receiving acknowledgment
        sock.settimeout(3)  # 3 seconds timeout
        try:
            acknowledgment, _ = sock.recvfrom(1024)
            print(f"ACK: {acknowledgment.decode()}")
            message = f"GET_STATE: request for state from {NAME}!"
            sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
            break  # Exit the loop if acknowledgment received
        except socket.timeout:
            print("Resending the request.")
            retry_count += 1
            continue  # Continue to next iteration without waiting

    if retry_count == RESEND_ATTEMP:
        print("I'm alone.")
        getStateFromLocal()

if __name__ == "__main__":
    # Start peer communication thread

    communication_thread = threading.Thread(target=peer_communication)
    communication_thread.start()

    # Start peer broadcasting thread
    broadcast_thread = threading.Thread(target=greeting_broadcast)
    broadcast_thread.start()

    # Keep main thread running
    communication_thread.join()
    broadcast_thread.join()