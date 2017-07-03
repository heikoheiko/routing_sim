"""
Network Backbone:

- Nodes connnect in a Kademlia style fashion but not strictly
- Light clients connect to full nodes

Tests:
- Test nodes doing a recursive path lookup
- Test nodes maintaining a view on the capacity up to n hops distance
- Test global path finding helper
- Count number of messages
- Count success rate
- Compare path length

Implement:
- Creation of the Network + storage/load of it
- power distribution of capacity
- flexible framework to simulate

Todo:
* variation of channel deposits
* preference for channel partners with similar deposits
* add light clients
* visualize deposits, light clients
* variation of capacities
* imprecise kademlia for sybill attacks prevention and growth of network
* locally cached neighbourhood capacity
* simulate availabiliy of nodes
* stats on global and recursive path finding

* calc the number of messages sent for global, locally cached and recursive routing
* 3d visualization of the network (z-axis being the deposits)


Interactive:
* rebalancing fees, fee based routing

"""

import networkx as nx
from dijkstra_weighted import dijkstra_path
import random
import sys
from utils import WeightedDistribution, draw3d, export_obj


random.seed(43)
sys.setrecursionlimit(100)


class ChannelView(object):

    "channel from the perspective of this"

    def __init__(self, this_node, other_node):
        assert isinstance(this_node, Node)
        assert isinstance(other_node, Node)
        assert this_node != other_node
        self.this = this_node.uid
        self.partner = self.other = other_node.uid
        if self.this < self.other:
            self._account = this_node.G.edge[this_node][other_node]
        else:
            self._account = this_node.G.edge[this_node][other_node]

    @property
    def balance(self):
        "what other owes self if positive"
        if self.this < self.other:
            return self._account['balance']
        return -self._account['balance']

    @balance.setter
    def balance(self, value):
        if self.this < self.other:
            self._account['balance'] = value
        else:
            self._account['balance'] = -value

    @property
    def deposit(self):
        return self._account[self.this]

    @deposit.setter
    def deposit(self, value):
        assert value >= 0
        self._account[self.this] = value

    @property
    def partner_deposit(self):
        return self._account[self.other]

    @property
    def capacity(self):
        return self.balance + self.deposit

    def __repr__(self):
        return '<Channel({}:{} {}:{} balance:{}>'.format(self.this, self.deposit,
                                                         self.other, self.partner_deposit)


class Node(object):

    min_deposit_deviation = 0.5  # accept up to X of own deposit

    def __init__(self, cn, uid, num_channels=0, deposit_per_channel=100):
        assert isinstance(cn, ChannelNetwork)
        self.cn = cn
        self.G = cn.G
        self.uid = uid
        self.num_channels = num_channels
        self.deposit_per_channel = deposit_per_channel
        self.channels = []
        self.min_expected_deposit = self.min_deposit_deviation * self.deposit_per_channel

    def __repr__(self):
        return '<{}({} deposit:{} channels:{}/{})>'.format(
            self.__class__.__name__, self.uid, self.deposit_per_channel,
            len(self.channels), self.num_channels)

    @property
    def partners(self):  # all partners
        return [cv.partner for cv in self.channels]

    @property
    def targets(self):
        """
        geometrical distances with 1/3 of id space as max distance
        """
        distances = [2 * self.cn.max_id / 2**i / 3
                     for i in range(1, self.num_channels + 1)]
        return [(self.uid + d) % self.cn.max_id for d in distances]

    def initiate_channels(self):
        def node_filter(node):
            return bool(node.deposit_per_channel > self.min_expected_deposit)

        for target_id in self.targets:
            for node_id in self.cn.get_closest_node_ids(target_id, filter=node_filter):
                other = self.cn.node_by_id[node_id]
                accepted = other.connect_requested(self) and self.connect_requested(other)
                if accepted:
                    self.cn.add_edge(self, other)
                    self.setup_channel(other)
                    other.setup_channel(self)
                    break

    def channel_view(self, other):
        return ChannelView(self, other)

    def setup_channel(self, other):
        assert isinstance(other, Node)
        cv = self.channel_view(other)
        cv.deposit = self.deposit_per_channel
        cv.balance = 0
        self.channels.append(cv)

    def connect_requested(self, other):
        assert isinstance(other, Node)
        if other.deposit_per_channel < self.min_expected_deposit:
            # print "refused to connect", self, other, self.min_expected_deposit
            return
        if other in self.partners:
            return
        if other == self:
            return
        return True

    def _channels_by_distance(self, target_id, value):

        max_id = self.cn.max_id

        def _distance(cv):
            a, b = target_id, cv.partner
            d = abs(a - b)
            if d > max_id / 2:
                d = abs(max_id - d)
            return d

        cvs = sorted(self.channels, lambda a, b: cmp(_distance(a), _distance(b)))
        assert len(cvs) < 2 or _distance(cvs[0]) <= _distance(cvs[-1])
        return [cv for cv in cvs if cv.capacity >= value]

    def find_path_recursively(self, target_id, value, max_hops=50, visited=[]):
        """
        sort channels by distance to target, filter by capacity
        setting a low max_hops allows to implment breath first, yielding in shorter paths
        """
        contacted = 0  # how many nodes have been contacted
        if self in visited:
            return 0, []
        for cv in self._channels_by_distance(target_id, value):
            if cv.partner == target_id:  # if can reach target return [self]
                return 0, [self]
            if len(visited) == max_hops:
                return contacted, []  # invalid
            node = self.cn.node_by_id[cv.partner]
            try:
                c, path = node.find_path_recursively(target_id, value, max_hops, visited + [self])
                contacted += 1 + c
                if path:
                    return contacted, [self] + path
            except RuntimeError:  # recursion limit
                pass
        return contacted, []  # could not find path


class FullNode(Node):
    pass


class LightClient(Node):
    pass


class ChannelNetwork(object):

    max_id = 2**32
    # max_id = 100
    num_channels_per_node = 5  # outgoing

    def __init__(self):
        self.G = nx.Graph()
        self.node_by_id = dict()
        self.nodeids = []
        self.nodes = []

    def generate_nodes(self, config):
        # full nodes
        for i in range(config.fn_num_nodes):
            uid = random.randrange(self.max_id)
            num_channels = int(config.fn_num_channel_dist.random())
            deposit_per_channel = int(config.fn_deposit_dist.random())
            node = FullNode(self, uid, num_channels, deposit_per_channel)
            self.node_by_id[uid] = node

        self.nodeids = sorted(self.node_by_id.keys())
        self.nodes = [self.node_by_id[_uid] for _uid in self.nodeids]

    def connect_nodes(self):
        for node in self.nodes[:]:
            node.initiate_channels()
            if not node.channels:
                print "not connected", node
                self.nodeids.remove(node.uid)
                del self.node_by_id[node.uid]
            elif len(node.channels) < 2:
                print "weakly connected", node

    def add_edge(self, A, B):
        assert isinstance(A, Node)
        assert isinstance(B, Node)
        if A.uid < B.uid:
            self.G.add_edge(A, B)
        else:
            self.G.add_edge(B, A)

    def get_closest_node_id(self, target_id, filter=None):
        # prepare search space
        if filter:
            nodeids = [n for n in self.nodeids if filter(self.node_by_id[n])]
        else:
            nodeids = self.nodeids
        # recursively split id space in half
        start, end = 0, len(nodeids) - 1
        while end - start > 1:
            idx = start + (end - start) / 2

            if nodeids[idx] > target_id:
                end = idx
            else:
                start = idx
        assert end - start <= 1, (end, start)

        ds = abs(nodeids[start] - target_id)
        de = abs(nodeids[end] - target_id)
        idx = min((ds, start), (de, end))[1]  # FXIME, fails at id space end
        # assert abs(nodeids[idx] -
        #            target_id) <= abs(self._get_closest_node_id(target_id) - target_id)
        return nodeids[idx]

    def get_closest_node_ids(self, target_id, filter=None):
        "generator"
        cid = self.get_closest_node_id(target_id, filter)
        idx = self.nodeids.index(cid)

        def get_next(idx, inc=1):
            while True:
                idx = (idx + inc) % len(self.nodeids)
                nodeid = self.nodeids[idx]
                if filter(self.node_by_id[nodeid]):
                    return idx, nodeid

        lidx, lid = get_next(idx, inc=-1)
        ridx, rid = get_next(idx, inc=1)
        while True:
            if abs(lid - target_id) < abs(lid - target_id):
                yield lid
                lidx, lid = get_next(lidx, inc=-1)
            else:
                yield rid
                ridx, rid = get_next(ridx, inc=1)

    def _get_path_cost_function(self, value, hop_cost=1):
        """
        goal: from all possible paths, choose from the shortes with enough capacity
        """
        def cost_func_fast(a, b, _account):
            # this func should be as fast as possible, as it's called often
            # don't alloc memory
            if a.uid < b.uid:
                capacity = _account['balance'] + _account[a.uid]
            else:
                capacity = - _account['balance'] + _account[a.uid]
            assert capacity >= 0
            if capacity < value:
                return None
            return hop_cost
        return cost_func_fast

    def find_path_global(self, source, target, value):
        assert isinstance(source, Node)
        assert isinstance(target, Node)
        try:
            path = dijkstra_path(self.G, source, target, self._get_path_cost_function(value))
            return path
        except nx.NetworkXNoPath:
            return None

    def find_path_recursively(self, source, target, value):
        assert isinstance(source, Node)
        assert isinstance(target, Node)
        contacted = 0
        for max_hops in (50, 5, 10, 15, 50):  # breath first possible
            c, path = source.find_path_recursively(target.uid, value, max_hops)
            contacted += c
            if path:
                break
        if path:
            assert len(path) == len(set(path))  # no node visited twice
            return contacted, path + [target]
        return contacted, []


def test_basic_channel():
    cn = ChannelNetwork()
    a = Node(cn, 1)
    b = Node(cn, 2)
    cn.G.add_edge(a, b)
    channel_ab = a.channel_view(b)
    channel_ba = b.channel_view(a)

    channel_ab.deposit = 10
    channel_ba.deposit = 20
    channel_ab.balance = 2
    assert channel_ba.balance == -2
    assert channel_ab.capacity == 10 + 2
    assert channel_ba.capacity == 20 - 2


def setup_network(config):
    assert isinstance(config, BaseNetworkConfiguration)
    cn = ChannelNetwork()
    cn.generate_nodes(config)
    cn.connect_nodes()
    draw3d(cn)
    # export_obj(cn)
    return cn


def test_basic_network(config):
    cn = setup_network(config)
    draw(cn)


def test_global_pathfinding(config, num_paths=10, value=2):
    cn = setup_network(config)
    for i in range(num_paths):
        print "-" * 40
        source, target = random.sample(cn.nodes, 2)
        path = cn.find_path_global(source, target, value)
        print len(path), path
        draw(cn, path)
        contacted, path = cn.find_path_recursively(source, target, value)
        print len(path), path, contacted
        draw(cn, path)


def draw(cn, path=None):
    from utils import draw as _draw
    assert isinstance(cn, ChannelNetwork)
    _draw(cn, path)


class BaseNetworkConfiguration(object):
    # full nodes
    fn_num_nodes = 100
    fn_deposit_dist = WeightedDistribution(10,
                                           weighted_values=[(100, 30), (1000, 20), (10000, 10)])

    fn_deposit_dist.smoothen(10)
    fn_num_channel_dist = WeightedDistribution(5, weighted_values=[(10, 100)])
    # light clients
    lc_num_nodes = 10 * fn_num_nodes
    lc_deposit_dist = WeightedDistribution(1, weighted_values=[(10, 90), (100, 10)])
    lc_num_channel_dist = WeightedDistribution(1, weighted_values=[(1, 100)])

    def __init__(self, fn_num_nodes):
        self.fn_num_nodes = fn_num_nodes

##########################################################


if __name__ == '__main__':
    test_basic_channel()
    # test_basic_network()
    test_global_pathfinding(BaseNetworkConfiguration(1000), num_paths=5, value=2)
