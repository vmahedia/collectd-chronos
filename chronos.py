#! /usr/bin/python
# Copyright 2015 Kevin Lynch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collectd
import json
import urllib2

PREFIX = "chronos"
CHRONOS_HOST = "localhost"
CHRONOS_PORT = 4400
CHRONOS_URL = ""
VERBOSE_LOGGING = False
CLEAN_METRICS = True

def configure_callback(conf):
    """Received configuration information"""
    global CHRONOS_HOST, CHRONOS_PORT, CHRONOS_URL, VERBOSE_LOGGING, CLEAN_METRICS
    for node in conf.children:
        if node.key == 'Host':
            CHRONOS_HOST = node.values[0]
        elif node.key == 'Port':
            CHRONOS_PORT = int(node.values[0])
        elif node.key == 'Verbose':
            VERBOSE_LOGGING = bool(node.values[0])
        elif node.key == 'CleanMetrics':
            CLEAN_METRICS = bool(node.values[0])
        else:
            collectd.warning('chronos plugin: Unknown config key: %s.' % node.key)

    CHRONOS_URL = "http://" + CHRONOS_HOST + ":" + str(CHRONOS_PORT) + "/metrics"

    log_verbose('Configured with host=%s, port=%s, url=%s' % (CHRONOS_HOST, CHRONOS_PORT, CHRONOS_URL))


def read_callback():
    """Parse stats response from Chronos"""
    log_verbose('Read callback called')
    try:
        metrics = json.load(urllib2.urlopen(CHRONOS_URL, timeout=10))

        for group in ['gauges', 'meters', 'timers', 'counters']:
            for name,values in metrics.get(group, {}).items():
                for metric, value in values.items():
                    if not isinstance(value, basestring):
                        dispatch_stat('gauge', '.'.join((name, metric)), value)
    except urllib2.URLError as e:
        collectd.error('chronos plugin: Error connecting to %s - %r' % (CHRONOS_URL, e))


def dispatch_stat(type, name, value):
    """Read a key from info response data and dispatch a value"""
    if value is None:
        collectd.warning('chronos plugin: Value not found for %s' % name)
        return
    log_verbose('Sending value[%s]: %s=%s' % (type, name, value))

    val = collectd.Values(plugin='chronos')
    if CLEAN_METRICS:
        name_parts = name.split('.')
        name_parts.reverse()
        name = ".".join(name_parts)
    val.type = type
    val.type_instance = name
    val.values = [value]
    val.dispatch()


def log_verbose(msg):
    if not VERBOSE_LOGGING:
        return
    collectd.info('chronos plugin [verbose]: %s' % msg)

collectd.register_config(configure_callback)
collectd.register_read(read_callback)
