Vagrant.configure("2") do |config|
	config.vm.box = "ubuntu/trusty64"
	config.vm.provision :shell, path: "bootstrap.sh"
	config.vm.network "private_network", type: :dhcp
	config.vm.synced_folder “C:\ChassisInfoFetcher\CIF", "/home/ubuntu/ChassisInfoFetcher"

end