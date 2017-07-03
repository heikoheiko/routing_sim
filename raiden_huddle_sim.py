from __future__ import division

"""
most users will run light clients and will only have a channel with one full node
note, that we can built it in a way so that full nodes filter messages for light clients
"""
users = light_clients = 1000 ** 3
full_nodes = light_clients / 1000

# transfers per day
transfers_per_user_per_day = 10
transfers_per_user_per_second = 10 / (24 * 3600)
transfers_per_second = transfers_per_user_per_second * users

# online time
secs_per_transfer = 30
online_fraction_per_day = secs_per_transfer * transfers_per_user_per_day / (24 * 3600)
concurrent_users = online_fraction_per_day * users
concurrent_light_clients_per_full_node = concurrent_users / full_nodes


# messages
hops_per_transfer = 6
messages_per_transfer = hops_per_transfer + 2
message_size = 268 + (hops_per_transfer-1) * 2 * 32
messages_per_second = transfers_per_second * messages_per_transfer

# bandwith restrictions
bps_light_client = 1/8 * 1024**2  # 1 MBit
bps_full_node = 16/8 * 1024**2  # 16 MBit

max_messages_per_second_light_client = bps_light_client / message_size
max_messages_per_second_full_node = bps_full_node / message_size

# huddle size
#max_transfers_per_huddle_per_second = max_messages_per_second_full_node / messages_per_transfer
#max_users_per_huddle = max_transfers_per_huddle_per_second / transfers_per_user_per_second
# huddles = full_nodes / max_users_per_huddle
huddles = messages_per_second / max_messages_per_second_light_client
max_users_per_huddle = users / huddles
full_nodes_per_huddle = full_nodes / huddles


print "transfers per second", transfers_per_second
print "concurrent_users", concurrent_users
print "concurrent_light_clients_per_full_node", concurrent_light_clients_per_full_node
print "messages per second", transfers_per_second * messages_per_transfer
print "message_size", message_size
print "max_messages_per_second_full_node", max_messages_per_second_full_node, max_messages_per_second_full_node * message_size
print "max_messages_per_second_light_client", max_messages_per_second_light_client
print "max_users_per_huddle", max_users_per_huddle
print "full_nodes_per_huddle", full_nodes_per_huddle
print "huddles", huddles


"""
thoughts:
- use whisper network per huddle
- use whisper and huddles are based around similar pubkeys
- note: nodes need to listen to messages from other huddles too!!!
- also note: nodes can ask their peers to deliver messages from other huddles to them
- or better some node they don't have a channel with, light client style ...
- super note: we don't want the channel partners to know our endpoint!!! not anyone!
- for spam protection use RDN token instad of PoW (if centralized message broker), though sha3 pow might be easier ...

huddles should be local on messaging and transfers

"""
Message requirements:
    Doing transfers with channel partners:
    - ideally direct connections(long lasting) w / channel partners, w/o them learning their endpoints

    Looking up paths:
    - com with distant nodes

    Broadcasting channel capacities:
    - send to




Scalable Routing:
- Full Nodes open channels Kademlia style
- PHS covering certain address segments
- Nodes broadcast their updated channel capacity + pings


Messaging:
- Nodes publish address->pubkey
- Nodes can derive a shared secret which when hashed becomes their topic
- Nodes listen to all their topics using whisper(where they can trade-off bandwidth for security)
    - even channel partners don't learn each others endpoints


"""



dfsdaf
"""
