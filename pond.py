import socket
import threading
import struct
import time
import os
import netifaces as ni
import services

# Multicast configuration
MULTICAST_GROUP = '224.1.1.1'   
MULTICAST_PORT = 5007
MULTICAST_TTL = 2

NAME = "Eq"
RESEND_ATTEMP = 3
ALONE_STATUS = True

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

        print(f"Received multicast message from {sender_ip}:", data.decode())
        acknowledgment_message = f"ACK from {NAME}'s notebook"
        sock.sendto(acknowledgment_message.encode(), address)

# Peer broadcasting using multicast
def greeting_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

    message = f"I'm {NAME}!"
    retry_count = 0
    while retry_count < RESEND_ATTEMP:  # Retry only twice
        sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
        print(f"Sent: {message}")

        # Set a timeout for receiving acknowledgment
        sock.settimeout(3)  # 3 seconds timeout
        try:
            acknowledgment, _ = sock.recvfrom(1024)
            print(f"Acknowledgment from receiver: {acknowledgment.decode()}")
            break  # Exit the loop if acknowledgment received
        except socket.timeout:
            print("Timeout occurred. Resending the request.")
            retry_count += 1
            continue  # Continue to next iteration without waiting

    if retry_count == RESEND_ATTEMP:
        print("No acknowledgment received after three retries. I'm alone.")

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
