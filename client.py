## client.py, used to run and test ICMP.py.
## must be run as root (using sudo).

from ICMP import *


## -- localhost (host = localhost) -- ##

# host = 'localhost'      ## 127.0.0.1
host = '127.0.0.1'

## -- UTokyo server (Asia) -- ##
## 119.245.132.49, dns2.nc.u-tokyo.ac.jp; NS for https://www.u-tokyo.ac.jp/en/ or UTokyo
host = '119.245.132.49'

## -- University of Melbourne server (Australia) -- ##
host = '43.245.41.9'
## 43.245.41.9, https://www.unimelb.edu.au/ 

## TODO: try hosts from all continents and combine into one test

## TODO: ignore this file and just run like this?
## sudo python3 -c 'from ICMP import *; ping("127.0.0.1")'

## -- ping the server -- ##
## ping the host
# delay = doOnePing(host, timeout=1)
delay = ping(host, timeout=1)
print(f'delay: {delay}')







'''
notes for testing

functionalities
    - correctly parses recieved packet's header fields
    - prints error message for what fields are not expected if not an
      expected ICMP reply message
    - computes the checksum (correctly) on received packet
    - adds and implements -c option
    - adds and implements -t option
    - calculates the min/max/avg RTTs
    - calculates packet loss %
    - parses ICMP response error codes, displays the error to user

specifications
    - tests localhost
    - tests servers in different continents


'''
