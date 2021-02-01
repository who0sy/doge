# coding: utf-8

import gevent
import pytest
from gevent.server import StreamServer

from doge.cluster.endpoint import EndPoint
from doge.cluster.ha import BackupRequestHA, FailOverHA
from doge.cluster.lb import RandomLB
from doge.common.context import Context
from doge.common.doge import Request
from doge.common.url import URL
from doge.rpc.server import DogeRPCServer


class SumServer:
    def sum(self, x, y):
        return x + y


@pytest.fixture(scope="module")
def lb():
    url = URL("127.0.0.1", 4399, "")
    ep = EndPoint(url)
    return RandomLB(url, [ep])


@pytest.fixture(scope="function")
def server():
    server = StreamServer(
        ("127.0.0.1", 4399),
        DogeRPCServer(
            Context(URL(None, None, None, {"name": ""}), URL(None, None, None, {})),
            SumServer,
        ),
    )
    g = gevent.spawn(server.serve_forever)
    gevent.sleep(0.1)
    yield server
    g.kill()


class TestFailOverHA:
    def test_fail_over(self, server, lb):
        ha = FailOverHA(lb.url)
        r = Request("", "sum", 1, 2)
        assert ha.call(r, lb).value == 3


class TestBackupRequestHA:
    def test_br(self, server, lb):
        ha = BackupRequestHA(lb.url)
        r = Request("", "sum", 1, 2)
        assert ha.call(r, lb).value == 3
        lb.url.set_param("sum.retries", 5)
        assert ha.call(r, lb).value == 3
