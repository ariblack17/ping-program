## test-ICMP.py, a program meant to run a few simple tests on the main
## program to see if it is able to run (with command line options) connecting
## to servers from each continent.

from ICMP import *

## -- set host/server IPs -- ##
host_local  = '127.0.0.1'       ## local host
host_au     = '1.1.1.1'         ## cloudflare (AU)
host_eu     = '9.9.9.9'         ## quad9 (switzerland)
host_as     = '203.248.252.2'   ## korea telecom (korea)
host_sa     = '200.49.130.41'   ## telefonica (argentina)
host_af     = '197.155.77.1'    ## liquid telecom (kenya)

hosts = [host_local, host_as, host_au, host_eu, host_af, host_sa]

## -- ping each host -- ##
for host in hosts:
    ping(host, 3, 2)    ## ping the host; -t = 3; -c = 5
