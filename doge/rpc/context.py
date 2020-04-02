# coding: utf-8

from typing import Any, Dict, List, Union

from doge.cluster.endpoint import EndPoint
from doge.cluster.ha import BackupRequestHA, FailOverHA
from doge.cluster.lb import RandomLB, RoundrobinLB
from doge.common.url import URL
from doge.filter import FilterChain
from doge.registry.registry import DirectRegistry, EtcdRegistry


class Context(object):
    def __init__(self, url: URL, registry_url: URL) -> None:
        self.url = url
        self.registry_url = registry_url

    def get_registry(self) -> Any:  # TODO 定义Registry
        protocol = self.registry_url.get_param("protocol", "etcd")
        if protocol == "etcd":
            return EtcdRegistry(self.registry_url)
        elif protocol == "direct":
            return DirectRegistry(self.registry_url)

    def get_endpoints(
        self, registry: Any, service: str
    ) -> Union[Dict[int, EndPoint], Dict[str, EndPoint]]:
        eps = {}
        for k, v in registry.discovery(service).items():
            eps[k] = new_endpoint(k, v)
        return eps

    def get_ha(self) -> Union[FailOverHA, BackupRequestHA]:
        name = self.url.get_param("haStrategy", "failover")
        if name == "failover":
            return FailOverHA(self.url)
        elif name == "backupRequestHA":
            return BackupRequestHA(self.url)

    def get_lb(self, eps: List[EndPoint]) -> Union[RoundrobinLB, RandomLB]:
        name = self.url.get_param("loadBalance", "RoundrobinLB")
        if name == "RandomLB":
            return RandomLB(self.url, eps)
        elif name == "RoundrobinLB":
            return RoundrobinLB(self.url, eps)

    def get_filter(self, executer: Any) -> Any:  # TODO 定义Executer
        return FilterChain(self).then(executer)


def new_endpoint(k: Union[int, str], v: str) -> EndPoint:
    host, port = v.split(":")
    url = URL(str(host), int(port), k)
    return EndPoint(url)
