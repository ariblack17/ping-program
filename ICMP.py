## ICMP.py, the client program for our implementation of ping.
##
## tests whether a host is reachable across an IP network and the latency
## using ICMP

from socket import *
import os
import sys
import struct
import time
import select
import binascii  
import argparse
import ipaddress


ICMP_ECHO_REQUEST = 8
FORMAT_HEADER = "bbHHh"
FORMAT_DATA = 'd'

## helper function
def MyChecksum(hexlist):
	''' computes and returns a checksum over some data (type hexlist). '''
	summ=0
	carry=0

	for i in range(0,len(hexlist),2):
		summ+=(hexlist[i]<< 8)  + hexlist[i+1]
		carry=summ>>16
		summ=(summ & 0xffff)  + carry
		#print(str(hex((hexlist[i]<< 8)  + hexlist[i+1]))+" "+str(hex(summ)) + "  " +str(hex(carry)) + " " + str(hex(summ^0xffff)))

	while( summ != (summ & 0xffff)):
		carry=summ>>16
		summ=summ & 0xffffffff  + carry
		#print("loop loop")

	summ^=0xffff #invert it
	return summ

## helper function
def checksum(string): 
	''' computes and returns a checksum over some data (type string). '''
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + ord(string[len(string) - 1])
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	#print(hex(answer))
	#print(hex(checksum0(string)))
	return answer
	
## helper function
def receiveOnePing(mySocket, ID, timeout, destAddr):
	''' receives a ping from the server/host and unpack the data.
		--
	 	ping structure: type, code, checksum, ID, seq. no
		reply type: 0
		reply code: 0
		reply data: includes all request data
	'''
	timeLeft = timeout
	
	while 1: 
		startedSelect = time.time()
		whatReady = select.select([mySocket], [], [], timeLeft)
		howLongInSelect = (time.time() - startedSelect)
		if whatReady[0] == []: # Timeout
			return "Request timed out." 
	
		timeReceived = time.time() 
		recPacket, addr = mySocket.recvfrom(1024)
		# print(f'rec: {recPacket}, {addr}')
	       
		#Fill in start
	
		# Fetch the ICMP header from the IP packet (get header)
		## (packet header: first 8 bytes)
		## (IP header: first 160b/20B of header)
		## (ICMP header: remainder of header after 160b/20B)

		## extract header from packet
		icmp_header = recPacket[20:28]	## 8 byte header, after 20B of IP header

		## unpack the header to read its values
		icmp_header = struct.unpack(FORMAT_HEADER, icmp_header)

		## extract data from packet
		data = recPacket[28:]	## the remaining bytes

		## unpack the data to read its values
		data = struct.unpack(FORMAT_DATA, data)

		## unpack the received tuples
		time_sent = data[0]										## data tuple
		r_type, r_code, r_checksum, r_ID, r_seq = icmp_header	## header tuple


		## parse for ICMP error codes
		
		## note: there are too many error codes and descriptions to feasibly
		## write out each descriptor, so the error type and code are returned for all
		## received error packets. Descriptions are given for the examples listed
		## in the assignment pdf.

		icmp_error = f'Error type {r_type} code {r_code}: '

		## check if dest IPv4 (different codes than IPv6)
		if ipaddress.ip_address(destAddr).version == 4:
			if r_type == 3: 
				if r_code == 0: icmp_error += 'Destination Network Unreachable'
				elif r_code == 1: icmp_error += 'Destination Host Unreachable'
				else:
					icmp_error += 'Destination Unreachable'
				
			elif r_type == 5: icmp_error += 'Redirect'
			elif r_type == 11: icmp_error += 'Time Exceeded'
			elif r_type == 12: icmp_error += 'Parameter Problem'
			elif r_type == 4: icmp_error += 'Source Quench'

		## else if dest IPv6
		else:
			if r_type == 1: icmp_error += 'Destination Unreachable'
			elif r_type == 2: icmp_error += 'Packet Too Big'
			elif r_type == 3: icmp_error += 'Time Exceeded'
			elif r_type == 4: icmp_error += 'Parameter Problem'

		## display error if not type 0 (success)
		if r_type != 0:
			print(f'ICMP error code received.\n{icmp_error}')

		## re-calculate the checksum for verification (taken from template code given below)
		new_header = struct.pack(FORMAT_HEADER, r_type, r_code, 0, r_ID, r_seq)	## pack header
		new_data = struct.pack("d", time_sent)									## pack data
		new_checksum = MyChecksum ([i for i in new_header] + [i for i in new_data])	## calculate checksum
		# Get the right checksum, and put in the header
		if sys.platform == 'darwin': new_checksum = htons(new_checksum) & 0xffff		
		else: new_checksum = htons(new_checksum)

		# r_ID = 1
		# destAddr = 1
		# r_checksum = 1

		## check that this is an expected ICMP reply message
		## (ID, destination, checksum)
		error = ''
		if r_ID != ID: error += 'Incorrect ID received. '
		if addr[0] != destAddr: error += 'Incorrect address received. '
		if new_checksum != r_checksum: error += 'Incorrect checksum received. '
		if error != '': raise RuntimeError(error)	## raise error if any true

		## calculate time difference RTT
		ping_time = timeReceived - time_sent	## calculate ping time
		return ping_time
			
		# ## output to console
		# print(f'header received: {icmp_header}')
		# print(f'data received: {data}')


        
       	#Fill in end
		timeLeft = timeLeft - howLongInSelect
		if timeLeft <= 0:
			return "Request timed out."
	
## helper function
def sendOnePing(mySocket, destAddr, ID):
	''' sends a ping to the server/host. computes checksum over data, packs header.
		--
	 	ping structure: type, code, checksum, ID, seq. no
		request type: 8
		request code: 0
	'''
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	
	myChecksum = 0
	
        # Make a dummy header with a 0 checksum
	# struct -- Interpret strings as packed binary data

	## 	pack args: format, v1, v2, ...
	## 	format types: b (bits), d (binary64), 
	## 				  h (short int signed), H (short int unsigned)
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
    
	# Calculate the checksum on the data and the dummy header.
	#myChecksum = checksum(str(header + data))
	myChecksum = MyChecksum ([i for i in header] + [i for i in data])
	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		# Convert 16-bit integers from host to network  byte order
		myChecksum = htons(myChecksum) & 0xffff		
	else:
		myChecksum = htons(myChecksum)
		
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data

	# print(f'header length pre-ping: {len(header)}')
	# print(f'data length pre-ping: {len(data)}')
	
	# print(f'packet length pre-ping: {len(packet)}')

	# print(f'header (raw) pre-ping: {header}')
	# print(f'data (raw) pre-ping: {data}')
	
	mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
	# Both LISTS and TUPLES consist of a number of objects
	# which can be referenced by their position number within the object.
	
## helper function
def doOnePing(destAddr, timeout): 
	''' sends and receives a ping to/from the server/host. creates socket, gets
		ID, and calls helper functions.
		--
	'''
	icmp = getprotobyname("icmp")
	# SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw

	mySocket = socket(AF_INET, SOCK_RAW, icmp)
	
	myID = os.getpid() & 0xFFFF  # Return the current process i
	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	
	mySocket.close()
	return delay
	
def ping(host, timeout=1, c=None):
	''' sends and receives a ping to/from the server/host. creates socket, gets
		ID, and calls helper functions. returns the delay
		--
		also takes in command line args c (number messages) and timeout (TTL)

	'''
	# timeout=1 means: If one second goes by without a reply from the server,
	# the client assumes that either the client's ping or the server's pong is lost
	dest = gethostbyname(host)
	print("Pinging " + dest + " using Python:")
	print("")
	# Send ping requests to a server separated by approximately one second
	min_RTT, max_RTT = float('inf'), float('-inf')
	t_RTT, r_RTT, sum_RTT = 0, 0, 0	## transmitted/received packets, sum
	while 1 :

		## check c value
		if c and t_RTT >= c:
			break	## stop sending pings if finished

		## calculate current delay
		# if t: delay = doOnePing(dest, t)	## set timeout to TTL
		# else: delay = doOnePing(dest, timeout)
		delay = doOnePing(dest, timeout)

		## update statistics
		# print(t_RTT, c)
		t_RTT += 1	## count for avg
		if type(delay) != str:	## if a pkt is lost, returns a string
			if delay < min_RTT: min_RTT = delay	## min
			if delay > max_RTT: max_RTT = delay	## max
			sum_RTT += delay					## sum for avg
			r_RTT += 1

		
		## output most recent delay
		print(f'RTT: {delay}')

		## sleep to continue
		time.sleep(1)# one second

	## calculate statistics
	packet_loss = ((t_RTT - r_RTT) / t_RTT) * 100
	if r_RTT: avg_RTT = sum_RTT / r_RTT
	else: avg_RTT = 0		## edge case: if no packets received

	## output statistics
	print(f'--- {dest} ping statistics ---')
	print(f'{t_RTT} packets transmitted, {r_RTT} packets received,', end=' ') 
	print(f'{packet_loss}% packet loss, {avg_RTT} average RTT')

	return delay

if __name__ == '__main__':
	''' accept command line arguments to run the ping program.
	 	basic format: (sudo) python3 ICMP.py ping hostname
		flag: -c (specify the number of ping messages sent)
		flag: -t (specify the TTL for each ping message)
	'''

	## create an ArgumentParser object for parsing args
	parser = argparse.ArgumentParser()


	## add command line options
	parser.add_argument('method')
	parser.add_argument('host')
	parser.add_argument('-c', '--count')
	parser.add_argument('-t', '--ttl')

	## parse received arguments
	args = parser.parse_args()

	## parse method name		
	method = globals()[args.method] ## to get the method matching the string input

	## parse host IP
	host = args.host

	## parse echo request messages count
	if args.count:
		## specifies the number of echo request messages
		requests_count = int(args.count)
		print(f'requests count: {requests_count}')

	## parse TTL
	if args.ttl:
		## explicitly sets TTL
		requests_ttl = int(args.ttl)
		print(f'ttl: {requests_ttl}')


	method(host, requests_ttl, requests_count)


