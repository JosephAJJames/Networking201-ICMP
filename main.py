#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import datetime
import socket
import os
import sys
import struct
import time
import random
import traceback  # useful for exception handling
import threading


# NOTE: Do not import any other modules - the ones above should be sufficient

def setupArgumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='A collection of Network Applications developed for SCC.203.')
    parser.set_defaults(func=ICMPPing, hostname='lancaster.ac.uk')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_p = subparsers.add_parser('ping', aliases=['p'], help='run ping')
    parser_p.set_defaults(timeout=2, count=10)
    parser_p.add_argument('hostname', type=str, help='host to ping towards')
    parser_p.add_argument('--count', '-c', nargs='?', type=int,
                          help='number of times to ping the host before stopping')
    parser_p.add_argument('--timeout', '-t', nargs='?',
                          type=int,
                          help='maximum timeout before considering request lost')
    parser_p.set_defaults(func=ICMPPing)

    parser_t = subparsers.add_parser('traceroute', aliases=['t'],
                                     help='run traceroute')
    parser_t.set_defaults(timeout=2, protocol='icmp')
    parser_t.add_argument('hostname', type=str, help='host to traceroute towards')
    parser_t.add_argument('--timeout', '-t', nargs='?', type=int,
                          help='maximum timeout before considering request lost')
    parser_t.add_argument('--protocol', '-p', nargs='?', type=str,
                          help='protocol to send request with (UDP/ICMP)')
    parser_t.set_defaults(func=Traceroute)

    parser_w = subparsers.add_parser('web', aliases=['w'], help='run web server')
    parser_w.set_defaults(port=8080)
    parser_w.add_argument('--port', '-p', type=int, nargs='?',
                          help='port number to start web server listening on')
    parser_w.set_defaults(func=WebServer)

    parser_x = subparsers.add_parser('proxy', aliases=['x'], help='run proxy')
    parser_x.set_defaults(port=8000)
    parser_x.add_argument('--port', '-p', type=int, nargs='?',
                          help='port number to start web server listening on')
    parser_x.set_defaults(func=Proxy)

    args = parser.parse_args()
    return args


class NetworkApplication:

    def checksum(self, dataToChecksum: bytes) -> int:
        csum = 0
        countTo = (len(dataToChecksum) // 2) * 2
        count = 0

        while count < countTo:
            thisVal = dataToChecksum[count + 1] * 256 + dataToChecksum[count]
            csum = csum + thisVal
            csum = csum & 0xffffffff
            count = count + 2

        if countTo < len(dataToChecksum):
            csum = csum + dataToChecksum[len(dataToChecksum) - 1]
            csum = csum & 0xffffffff

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)

        answer = socket.htons(answer)

        return answer

    def printOneResult(self, destinationAddress: str, packetLength: int, time: float, seq: int, ttl: int,
                       destinationHostname=''):
        if destinationHostname:
            print("%d bytes from %s (%s): icmp_seq=%d ttl=%d time=%.3f ms" % (
            packetLength, destinationHostname, destinationAddress, seq, ttl, time))
        else:
            print("%d bytes from %s: icmp_seq=%d ttl=%d time=%.3f ms" % (
            packetLength, destinationAddress, seq, ttl, time))

    def printAdditionalDetails(self, packetLoss=0.0, minimumDelay=0.0, averageDelay=0.0, maximumDelay=0.0):
        print("%.2f%% packet loss" % (packetLoss))
        if minimumDelay > 0 and averageDelay > 0 and maximumDelay > 0:
            print("rtt min/avg/max = %.2f/%.2f/%.2f ms" % (minimumDelay, averageDelay, maximumDelay))

    def printOneTraceRouteIteration(self, ttl: int, destinationAddress: str, measurements: list,
                                    destinationHostname=''):
        latencies = ''
        noResponse = True
        for rtt in measurements:
            if rtt is not None:
                latencies += str(round(rtt, 3))
                latencies += ' ms  '
                noResponse = False
            else:
                latencies += '* '

        if noResponse is False:
            print("%d %s (%s) %s" % (ttl, destinationHostname, destinationAddress, latencies))
        else:
            print("%d %s" % (ttl, latencies))


class ICMPPing(NetworkApplication):

    def receiveOnePing(self, icmpSocket, destinationAddress, ID, timeout):
        icmpSocket.listen(1)
        con, addr = icmpSocket.accept()
        
        pass

    def sendOnePing(self, icmpSocket, destinationAddress, ID):
        print(destinationAddress)
        icmp_header = struct.pack("!BBHHH", 8, 0, 0, ID, ID)  # First packing
        checksum = self.checksum(icmp_header)  # Calculate checksum
        icmp_header = struct.pack("!BBHHH", 8, 0, checksum, ID, ID)  # Second packing with correct checksum
        port = 8000
        print(icmp_header)
        icmpSocket.sendto(icmp_header, (destinationAddress, port))
        return time.time()
        pass

    def doOnePing(self, destinationAddress, packetID, seq_num, timeout):
        # 1. Create ICMP socket
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        port = 8000
        icmp_socket.bind(("127.0.0.1", port))
        print("binding socket....")
        # 2. Call sendOnePing function
        self.sendOnePing(icmp_socket, destinationAddress, packetID)
        # 3. Call receiveOnePing function
        #self.receiveOnePing(icmp_socket, destinationAddress, packetID, timeout)
        # 4. Close ICMP socket
        icmp_socket.close()
        print("socket closed")
        # 5. Print out the delay (and other relevant details) using the printOneResult method, below is just an example.
        self.printOneResult(destinationAddress, 8, time.time(), packetID, timeout)  # Example use of printOneResult - complete as appropriate
        pass

    def __init__(self, args):
        print('Ping to: %s...' % (args.hostname))
        # 1. Look up hostname, resolving it to an IP address
        ip_address = socket.gethostbyname(args.hostname)
        print(ip_address)
        # 2. Repeat below args.count times
        # 3. Call doOnePing function, approximately every second, below is just an example
        for x in range(0, args.count):
            self.doOnePing(ip_address, x, x, 2)


class Traceroute(NetworkApplication):

    def __init__(self, args):
        print('Traceroute to: %s...' % (args.hostname))


class WebServer(NetworkApplication):

    def handleRequest(tcpSocket):
        # 1. Receive request message from the client on connection socket
        # 2. Extract the path of the requested object from the message (second part of the HTTP header)
        # 3. Read the corresponding file from disk
        # 4. Store in temporary buffer
        # 5. Send the correct HTTP response error
        # 6. Send the content of the file to the socket
        # 7. Close the connection socket
        pass

    def __init__(self, args):
        print('Web Server starting on port: %i...' % (args.port))
        # 1. Create server socket
        # 2. Bind the server socket to server address and server port
        # 3. Continuously listen for connections to server socket
        # 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
        # 5. Close server socket


class Proxy(NetworkApplication):

    def __init__(self, args):
        print('Web Proxy starting on port: %i...' % (args.port))


# Do not delete or modify the code below
if __name__ == "__main__":
    args = setupArgumentParser()
    args.func(args)
