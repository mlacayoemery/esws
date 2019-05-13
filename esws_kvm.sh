sudo virt-install --name ESWS --ram=4096 --vcpus=2 --cpu host --hvm --disk path=/var/lib/libvirt/images/ESWS,size=30 --cdrom /data/install/debian-9.6.0-amd64-DVD-1.iso --graphics vnc
