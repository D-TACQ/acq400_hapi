#!/usr/bin/env python3

import argparse
import os
from flask import Flask
import threading
import time
import json
import acq400_hapi
from acq400_hapi import afhba404
import logging

class globals:
	lock = threading.RLock()
	gatherer = None
	last_request = 0
	last_ident = 0
	connected_uuts = {}
	uuts = {}
	threads = {}

def get_parser():
	parser = argparse.ArgumentParser(description='Stream monitor webserver')
	parser.add_argument('--port', default=5000, help='Port to run webserver on')
	return parser

def run_main(args):
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	run_webserver(args)

def get_devices_states():
	while True:
		#print("Getting states")
		if time.time() - globals.last_ident > 60:
			globals.last_ident = time.time()
			globals.threads['ident'] = threading.Thread(target=get_connected_uuts)
			globals.threads['ident'].start()
		globals.lock.acquire()
		for dev in globals.connected_uuts.items():
			uut_name = dev[0]
			globals.threads[uut_name] = threading.Thread(target=get_remote_state,  args=(uut_name, ))
			globals.threads[uut_name].start()
			for lport in dev[1]['ports']:
				dev[1]['ports'][lport]['job_state'] = afhba404.get_stream_state(lport)._asdict()
		globals.lock.release()
		if time.time() - globals.last_request > 60:
			print('Monitor idle halting')
			globals.gatherer = None
			exit()
		time.sleep(1)

def get_connected_uuts():
	devs = afhba404.get_connections()
	globals.lock.acquire()
	for dev in devs.items():
		lport = dev[0]
		uut_name = dev[1].uut
		if uut_name not in globals.connected_uuts:
			globals.connected_uuts[uut_name] = {}
			globals.connected_uuts[uut_name]['uut_status'] = None
			globals.connected_uuts[uut_name]['last_query'] = 0
			globals.connected_uuts[uut_name]['ports'] = {}
		if lport not in globals.connected_uuts[uut_name]['ports']:
			globals.connected_uuts[uut_name]['ports'][lport] = {}
			globals.connected_uuts[uut_name]['ports'][lport]['job_state'] = {}
			globals.connected_uuts[uut_name]['ports'][lport]['connected'] = True
			globals.connected_uuts[uut_name]['ports'][lport]['rport'] = dev[1].cx
		if uut_name not in globals.uuts:
			try:
				globals.uuts[uut_name] = acq400_hapi.factory(dev[1].uut)
			except Exception as e:
				print(e)
	globals.lock.release()

def get_remote_state(uut_name):
	if time.time() - globals.connected_uuts[uut_name]['last_query'] < 5:
		exit()
	globals.connected_uuts[uut_name]['last_query'] = time.time()
	#print(f'Getting {uut_name} status')
	uut_status = globals.uuts[uut_name].s0.CONTINUOUS_STATE
	globals.lock.acquire()
	globals.connected_uuts[uut_name]['uut_status'] = uut_status.split(' ')[1]
	globals.lock.release()
	exit()

def check_still_connected():
	devs = afhba404.get_connections()
	connections = {}
	for dev in devs:
		connections[devs[dev].uut] = []
		connections[devs[dev].uut].append(int(devs[dev].dev))
	globals.lock.acquire()
	for uut_name in globals.connected_uuts.copy():
		if uut_name not in connections:
			print(f'removing {uut_name} as not connected')
			del globals.connected_uuts[uut_name]
			continue
		for lport in globals.connected_uuts[uut_name]['ports'].copy():
			if lport not in connections[uut_name]:
				print(f'removing {uut_name}:{lport} as not connected')
				del globals.connected_uuts[uut_name]['ports'][lport]
	globals.lock.release()

def run_webserver(args):
	app = Flask(__name__,)

	@app.route("/")
	def get_index():
		globals.last_ident = 0
		globals.last_request = time.time()
		if not globals.gatherer:
			globals.gatherer = threading.Thread(target=get_devices_states)
			globals.gatherer.start()
		t = threading.Thread(target=check_still_connected)
		t.start()
		#page = open("test.html", "r").read()
		return page

	@app.route("/state.json")
	def get_state():
		globals.last_request = time.time()
		if not globals.gatherer:
			print('Running')
			globals.gatherer = threading.Thread(target=get_devices_states)
			globals.gatherer.start()
		globals.lock.acquire()
		data = json.dumps(globals.connected_uuts)
		globals.lock.release()
		return data

	app.run(host="0.0.0.0", port=args.port, debug=True)

page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="google" value="notranslate">
    <title>afhba monitor</title>
    <style>
        body {
            background-color: #E8E9F3;
            font-family: "Courier New", Courier, monospace;
        }
        #template, .job_template{
            display: none;
        }
        .IDLE {
            color: red;
        }
        .RUN {
            color: greenyellow;
        }
        .ARM {
            color: orange;
        }
		.header{
			padding: 0px 10px;
			display: flex;
			align-items: center;
			justify-content: space-between;
		}
		.button{
			border: 1px solid black;
			padding: 4px;
			cursor: pointer;
		}
		#detailToggle{
			display: none;
		}
		#subtitle{
			margin-left: 5px;
			font-size: 16px;
		}
		#container{
            display: flex;
            flex-flow: row wrap;
        }
		.summary .conn_box{
			width: 100%;
		}
		.summary .device{
			display: flex;
			gap: 10px;
		}
		.summary .state{
			display: none;
		}
		.summary .spi{
			display: block;
		}
        .conn_box{
            background-color: #8395a7;
            font-size: 20px;
            margin: 2px;
            padding: 5px;
	    	color: #130f40;
        }
		.device{
			align-items: center;
		}
		.device a{
			text-decoration: none;
			color: #130f40;
		}
		.device a:hover{
			color: #f9ca24;
		}
		.spi{
			color: orange;
			display: none;
			text
		}
        .state{
            background-color: #c8d6e5;
            box-sizing: border-box;
            padding: 2px;
            width: 100%;
            font-size: 16px;
        }
        .rx, .rx_rate{
            font-weight: bold;
        }
    </style>
    <script>
        function main(){
            url = "state.json"
            if(document.visibilityState != "hidden"){
                get_state(url, build_conn_boxes);
            }
            setTimeout(main, 1000);
        }
        function get_state(url, callback){
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.responseType = 'json';
            xhr.onreadystatechange = function() {
                if(xhr.readyState == 4 && xhr.status == 200) {
                    callback(xhr.response);
            }
        }
            xhr.send();
        }
        function build_conn_boxes(data){
            template = document.getElementById('template');
            container = document.getElementById('container');
            container.innerHTML = "";
            for (const [key, value] of Object.entries(data)) {
                for (const [lport, lvalues] of Object.entries(value['ports'])) {
                    new_row = template.cloneNode(true);
                    new_row.id = "";
                    new_row.getElementsByClassName('uut_name')[0].innerText = key;
		    		new_row.getElementsByClassName('uut_name')[0].href = `http://${key}`;
                    new_row.getElementsByClassName('uut_status')[0].innerText = value['uut_status'];
                    new_row.getElementsByClassName('uut_status')[0].className = value['uut_status'];
                    new_row.getElementsByClassName('rport')[0].innerText = lvalues['rport'];
                    new_row.getElementsByClassName('hostname')[0].innerText = location.hostname;
                    new_row.getElementsByClassName('lport')[0].innerText = lport;
                    state = "";
                    job_template = new_row.getElementsByClassName('job_template')[0]
                    for (const [job_key, job_value] of Object.entries(lvalues['job_state'])) {
                        new_state = job_template.cloneNode(true);
                        new_state.className = job_key
                        new_state.firstChild.innerHTML = job_key
                        new_state.lastChild.innerHTML = job_value
                        new_row.getElementsByClassName('state')[0].appendChild(new_state);
                    }
                    container.appendChild(new_row);
                }
            }
        }
		function toggle_detail(event){
			event.target.labels[0].textContent = event.srcElement.checked ? 'Details..' : 'Summary..';
			document.getElementById('subtitle').textContent = event.srcElement.checked ? 'summary' : 'details';
			document.getElementById('container').className = event.srcElement.checked ? 'summary' : 'details';
		}
        window.onload = main();
    </script>
</head>
<body>
    <div class="conn_box" id="template">
        <div class="device">
            <div>[<span class="uut_status">uut_status</span>]</div>
            <div><a href="#" class="uut_name">uut_name</a>:<span class="rport">rport</span></div>
	    	<span class="spi">---></span>
            <div><span class="hostname">hostname</span>:<span class="lport">lport</span></div>
        </div>
        <table class="state">
            <tr class="job_template"><td>key</td><td>value</td></tr>
        </table>
    </div>
    <div class="header">
    	<h1>Afhba monitor<span id="subtitle">summary</span></h1>
		<input type="checkbox" checked id="detailToggle" onchange="toggle_detail(event)"></input>
		<label for="detailToggle" class="button">Details...</label>
	</div>
    <div id="container" class="summary">Loading...</div>
</body>
</html>
"""

if __name__ == '__main__':
	run_main(get_parser().parse_args())