name "default"

description "Sets up the minimum system requirements to run a general smac module."

run_list(
  "recipe[python]"
)

default_attributes :python => {
  
}

