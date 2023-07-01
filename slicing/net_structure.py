
class Mode:
    WORK_MODE = 0
    GAMING_MODE = 1
    WORK_EMERGENCY_MODE = 2

def mac( name: str ):

    host_map = {
        "h1": "00:00:00:00:00:01",
        "h2": "00:00:00:00:00:02",
        "h3": "00:00:00:00:00:03",
        "h4": "00:00:00:00:00:04",
        "h5": "00:00:00:00:00:05",

        "g1": "00:00:00:00:00:06",
        "g2": "00:00:00:00:00:07",

        "gs": "00:00:00:00:01:01",
        "ps": "00:00:00:00:01:02",
    }

    return host_map[ name.lower() ]

def all_macs():
   return [ mac("h1"), mac("h2"), mac("h3"), mac("h4"), mac("h5"), mac("g1"), mac("g2"), mac("gs"), mac("ps") ]
