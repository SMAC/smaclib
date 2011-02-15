name "dev"

description "Basic development machine"

run_list(
    "recipe[vim]",
    "recipe[build-essential]"
)

#default_attributes :name => "value"

