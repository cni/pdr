# launch a python shell, then

import ue9

# note: if the following fails, then check permissions on the LJ device
# node in /dev/bus/usb/NNN/NNN (where NNN/NNN might be 008/003).

lj=ue9.UE9()

lj.commConfig()  # will display the current settings

# to do DHCP:
lj.commConfig(DHCPEnabled=True)

# for a fixed IP:
lj.commConfig(DHCPEnabled=False,IPAddress='10.0.3.1',Gateway='0.0.0.0',Subnet='255.255.0.0')
lj.setDefaults()


