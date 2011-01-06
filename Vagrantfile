Vagrant::Config.run do |config|
    config.vm.box = "lucid32"

    # config.vm.network "33.1.1.1"

    config.vm.forward_port "mongodb", 27017, 27017
    config.vm.forward_port "redis", 6379, 6379

    # config.vm.share_folder("v-data", "/vagrant_data", "../data")

    config.vm.provisioner = :chef_solo

    config.chef.cookbooks_path = "conf/chef/cookbooks"
    config.chef.roles_path = "conf/chef/roles"

    config.chef.add_role "central_server"

    #config.chef.json.merge!({})
end
