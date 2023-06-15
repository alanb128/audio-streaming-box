#!/usr/bin/python3
#
# moOde audio player (C) 2014 Tim Curtis
# http://moodeaudio.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Stub script for lcd-updater.sh daemon
#

import requests
import socket
import subprocess

mydict = {}

with open("/var/local/www/currentsong.txt") as file1:
    for line in file1:
        mysplit = line.split("=")
        mydict[mysplit[0]] = mysplit[1].strip('\n')

#print(mydict)
mydict["h_name"] = socket.gethostname()
ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
mydict["ip"] = ips.decode().split()[0]
moode_ver = result = subprocess.run(['moodeutl', '--mooderel'], stdout=subprocess.PIPE)
mydict["moode_ver"] = result.stdout.decode('utf-8')
try:
    r = requests.post('http://localhost:8080', data=mydict)
except:
    pass

