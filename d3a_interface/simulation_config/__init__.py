

class SimulationConfigException(Exception):
    pass


def validate_simulation_config(simulation_config):
    if set(simulation_config.keys()) != \
            {"username", "name", "uuid", "domain_name",
             "web_socket_domain_name", "global_settings", "registry"}:
        raise SimulationConfigException(f"simulation_config doesn't have all the keys")
