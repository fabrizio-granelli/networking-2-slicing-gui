
class Mode:
    WORK_MODE = 0
    GAMING_MODE = 1
    WORK_EMERGENCY_MODE = 2

def mac( name: str ):

    host_map = {
        "h1": "10.0.0.1",
        "h2": "10.0.0.2",
        "h3": "10.0.0.3",
        "h4": "10.0.0.4",
        "h5": "10.0.0.5",

        "g1": "10.0.0.6",
        "g2": "10.0.0.7",

        "gs": "10.0.0.8",
        "ps": "10.0.0.9",
    }

    return host_map[ name.lower() ]

def all_macs():
   return [ mac("h1"), mac("h2"), mac("h3"), mac("h4"), mac("h5"), mac("g1"), mac("g2"), mac("gs"), mac("ps") ]


def all_switches():
    return [ "s1", "s2", "s3", "s4", "s5" ]
