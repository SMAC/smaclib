name "central-server"

description "Set up all services for the central communication server"

run_list(
    "recipe[mongodb]",
    "recipe[redis]",
    "recipe[rabbitmq]",
    "recipe[nginx]"
)

#default_attributes :name => "value"

