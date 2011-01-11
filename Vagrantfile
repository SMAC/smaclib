Vagrant::Config.run do |config|
    config.vm.box = "lucid32"

    # config.vm.network "33.1.1.1"

    config.vm.forward_port "mongodb", 27017, 20000
    config.vm.forward_port "mongodb-web-admin", 28017, 20001
    config.vm.forward_port "redis", 6379, 20002

    # config.vm.share_folder("v-data", "/vagrant_data", "../data")

    config.vm.provisioner = :chef_solo

    config.chef.cookbooks_path = "conf/chef/cookbooks"
    config.chef.roles_path = "conf/chef/roles"

    config.chef.add_role "central_server"

    config.chef.json.merge!({
        :mongodb => {:rest => true}
    })
end
