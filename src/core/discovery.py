import urllib.request
import json
from typing import List
from .interfaces import IDiscoveryService, SDRNode

class KiwiSDRDiscoveryService(IDiscoveryService):
    def fetch_nodes(self) -> List[SDRNode]:
        nodes = []
        try:
            print("Fetching public SDR nodes from rx.linkfanel.net...")
            req = urllib.request.Request("https://rx.linkfanel.net/snr.json", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0:
                        host = v[0]
                        port = 8073
                        if ":" in host:
                            parts = host.split(":")
                            host = parts[0]
                            port = int(parts[1])
                            
                        nodes.append(SDRNode(host=host, port=port, name=k))
        except Exception as e:
            print(f"Failed to fetch public nodes from linkfanel: {e}")
            try:
                print("Trying fallback rx.kiwisdr.com...")
                req = urllib.request.Request("http://rx.kiwisdr.com/snr.json", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0:
                            host = v[0]
                            port = 8073
                            if ":" in host:
                                parts = host.split(":")
                                host = parts[0]
                                port = int(parts[1])
                            nodes.append(SDRNode(host=host, port=port, name=k))
            except Exception as e2:
                print(f"Failed to fetch from kiwisdr.com: {e2}")
                print("Falling back to hardcoded highly-available nodes...")
                nodes = [
                    SDRNode(host="fenu-radio.ch", port=8073, name="FenuRadio (CH)"),
                    SDRNode(host="hf.g8jnj.net", port=8073, name="G8JNJ (UK)"),
                    SDRNode(host="hackgreensdr.org", port=8073, name="HackGreen (UK)"),
                    SDRNode(host="utahsdr.org", port=8073, name="UtahSDR (US)"),
                    SDRNode(host="southsdr.kiwisdr.com", port=8073, name="SouthSDR (US)")
                ]
        return nodes
