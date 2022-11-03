#!/usr/bin/env python

from __future__ import print_function
import threading
from threading import Thread
import argparse
import netifaces
import os
import sys
import time
import zmq

parser = argparse.ArgumentParser(prog='ip_mapper', description='IP address mapping program for DLS')
parser.add_argument('-H', '--host', type=str, default='127.0.0.1', help='Local host (local cluster-IP)')
parser.add_argument('-p', '--port', type=int, default=48000, help='Communication server port')
parser.add_argument('-i', '--interface', type=str, default='ib0', help='Destination interface device name')
parser.add_argument('-c', '--cluster', type=str, nargs='+', help='Cluster host list (all cluster-IPs)')
parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
parser.add_argument('-s', '--self', action='store_true', help='Check self IP')
parser.add_argument('-l', '--label', type=str, default='xxxxxx-00000000', help='Unique label')
parser.add_argument('-P', '--ping', action='store_true', help='Ping each host in result')
args, unparsed = parser.parse_known_args()

context = zmq.Context()
result = []
if args.cluster and args.host and args.host in args.cluster:
    task_index = args.cluster.index(args.host)
else:
    task_index = 0

BIND_RETRY_TIMES = 30
BIND_RETRY_INTERVAL = 5
CLIENT_RESP_TIMEOUT = 4
CLIENT_REQ_DELAY = 1
SUCCESS = 'SUCCESS'
FAILED = 'FAILED'
ORIGINAL_DEVICE_NAME = '0'


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def log(text):
    if not args.quiet:
        eprint('INFO: Task(%d) - %s' % (task_index, text))


def err(text):
    eprint('ERROR: Task(%d) - %s' % (task_index, text))


def get_ip(device):
    try:
        if device == ORIGINAL_DEVICE_NAME:
            if ':' in args.host:
                ip = args.host.split(':')[0]
            else:
                ip = args.host
        else:
            ip = netifaces.ifaddresses(device)[netifaces.AF_INET][0]['addr']
    except Exception as e:
        ip = '0.0.0.0'
        err(e)
    return ip


def get_port_listener(port):
    command = 'bash -c \"netstat -nlp 2> /dev/null | egrep \':%d\\>\' | head -1; ps -o args= -p `netstat -nlp 2> /dev/null | egrep \':%d\\>\' | head -1 | awk \'{print $7}\' | cut -d/ -f1` 2> /dev/null\"' \
              % (port, port)
    p = os.popen(command)
    listener = p.read().strip()
    p.close()
    return listener


def ping_hosts(host_list):
    output = ''
    for item in host_list:
        if ':' in item:
            host_port = item.split(':')
            host = host_port[0]
        else:
            host = item
        command = 'ping -w5 -W5 -c1 %s' % host
        p = os.popen(command)
        output += p.read()
        p.close()
    return output


def create_server_socket(port):
    server_socket = context.socket(zmq.REP)

    for retry in range(BIND_RETRY_TIMES):
        try:
            server_socket.bind('tcp://*:%d' % port)
            break
        except Exception as ex:
            err('Server: socket bind error (%s), will retry' % ex)
            time.sleep(BIND_RETRY_INTERVAL)
    else:
        err('Server: cannot bind socket, will exit')
        raise ValueError('failed to create server socket')

    return server_socket


def server_work(server_error_event):
    try:
        result_map = {}
        log('Server: starting at *:%d' % args.port)

        with create_server_socket(args.port) as server_socket:
            num = len(args.cluster)

            while True:
                log('Server: waiting for message')
                message = server_socket.recv()
                key_value = message.decode().split(',')
                key = key_value[0]
                value = key_value[1]
                label = key_value[2]
                if label == args.label:
                    server_socket.send(SUCCESS.encode('ascii', 'ignore'))
                    result_map[key] = value
                    log('Server: got match message %d/%d [%s]' % (len(result_map), num, message))
                else:
                    server_socket.send(FAILED.encode('ascii', 'ignore'))
                    log('Server: drop mismatch message %d/%d [%s]' % (len(result_map), num, message))

                if len(result_map) == num:
                    log('Server: got all messages')
                    break

            for item in args.cluster:
                if item in result_map:
                    result.append(result_map[item])
                    result_map.pop(item)
                else:
                    result.append('None')

            if (len(result_map) != 0) or (len(result) != num):
                err('Server: result number error')

    except Exception as e:
        server_error_event.set()
        err('Server: %s' % e)
    finally:
        log('Server: done')


def create_client_socket(host, port):
    client_socket = context.socket(zmq.REQ)
    target_server = 'tcp://%s:%d' % (host, port)
    log('Client: connecting to server %s' % target_server)
    client_socket.connect(target_server)
    client_socket.setsockopt(zmq.RCVTIMEO, CLIENT_RESP_TIMEOUT * 1000)
    client_socket.setsockopt(zmq.LINGER, 0)
    return client_socket


def client_work(server_error_event):
    try:
        log('Client: starting')
        message = args.host + ',' + get_ip(args.interface) + ',' + args.label

        for item in args.cluster:
            if ':' in item:
                host_port = item.split(':')
                host = host_port[0]
                port = int(host_port[1])
            else:
                host = item
                port = args.port

            while not server_error_event.is_set():

                with create_client_socket(host, port) as client_socket:

                    try:
                        log('Client: send message [%s]' % message)
                        client_socket.send(message.encode('ascii', 'ignore'))
                    except (TypeError, ValueError, zmq.ZMQError) as e:
                        err('Client: %s' % e)
                        break

                    try:
                        resp = client_socket.recv()

                        if resp.decode() == SUCCESS:
                            log('Client: got success response from server')
                            break
                        else:
                            log('Client: got failed response from server, '
                                'wait %d second and retry' % CLIENT_REQ_DELAY)
                            time.sleep(CLIENT_REQ_DELAY)
                            continue
                    except zmq.ZMQError:
                        log('Client: wait response timeout(%s) from server, retry'
                            % CLIENT_RESP_TIMEOUT)
                        continue

    except Exception as e:
        err('Client: %s' % e)
    finally:
        log('Client: done')


def self_work():
    log('Self: starting')
    result.append(get_ip(args.interface))


if __name__ == '__main__':
    log('Main: ip_mapper starting with %s' % args)

    if args.self:
        try:
            self_work()
        except Exception as e:
            err('Main: %s' % e)

    else:
        listener = get_port_listener(args.port)
        if listener != '':
            err('Main: port %d is using by [%s]' % (args.port, listener))
        try:
            server_error_event = threading.Event()
            server_thread = Thread(target=server_work, args=(server_error_event, ))
            server_thread.start()
            client_work(server_error_event)
            server_thread.join()
        except Exception as e:
            err('Main: %s' % e)

    if args.ping:
        ping_output = ping_hosts(result)
        log('Main: ping output: %s' % ping_output)

    for item in result:
        print(item)

    context.destroy(linger=0)
    log('Main: done')
