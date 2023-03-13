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
		print("Getting states")
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
			print('Thread idle killing self')
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
	print(f'Getting {uut_name} status')
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
		connections[devs[dev].uut].append(devs[dev].dev)
	globals.lock.acquire()
	for uut_name in globals.connected_uuts.copy():
		if uut_name not in connections:
			print(f'removing {uut_name}')
			del globals.connected_uuts[uut_name]
			continue
		for lport in globals.connected_uuts[uut_name]['ports'].copy():
			if lport not in connections:
				print(f'removing {uut_name}:{lport}')
				del globals.connected_uuts[uut_name]['ports'][lport]
	globals.lock.release()

page = """
<!DOCTYPE html><html lang="en"><head><meta name="google" value="notranslate"><title>afhba monitor</title><style>body{background-color:#e8e9f3;font-family:"Courier New",Courier,monospace}#template,.job_template{display:none}.IDLE{color:red}.RUN{color:#adff2f}.ARM{color:orange}.conn_box{background-color:#8395a7;font-size:16px;margin-bottom:10px;overflow:auto}.devs{font-size:20px;margin-bottom:0;padding:5px 10px;display:flex}.spi{padding:0 10px;color:orange}.state{background-color:#c8d6e5;margin:5px 5px;padding:2px;word-wrap:break-word}.state>span{margin-right:5px}.rx,.rx_rate{font-weight:700}</style><script>function main(){url="state.json","hidden"!=document.visibilityState&&get_state(url,callback),setTimeout(main,1e3)}function get_state(e,t){var n=new XMLHttpRequest;n.open("GET",e,!0),n.responseType="json",n.onreadystatechange=function(){4==n.readyState&&200==n.status&&t(n.response)},n.send()}function callback(e){for(let[t,n]of(template=document.getElementById("template"),(container=document.getElementById("container")).innerHTML="",Object.entries(e)))for(let[s,a]of Object.entries(n.ports)){for(let[l,o]of((new_row=template.cloneNode(!0)).id="",new_row.getElementsByClassName("uut_name")[0].innerText=t,new_row.getElementsByClassName("uut_status")[0].innerText=n.uut_status,new_row.getElementsByClassName("uut_status")[0].className=n.uut_status,new_row.getElementsByClassName("rport")[0].innerText=a.rport,new_row.getElementsByClassName("hostname")[0].innerText=location.hostname,new_row.getElementsByClassName("lport")[0].innerText=s,state="",job_template=new_row.getElementsByClassName("job_template")[0],Object.entries(a.job_state)))(new_state=job_template.cloneNode(!0)).className=l,new_state.firstChild.innerHTML=l+"=",new_state.lastChild.innerHTML=o,new_row.getElementsByClassName("state")[0].appendChild(new_state);container.appendChild(new_row)}}window.onload=main();</script></head><body><h1>afhba monitor</h1><div class="conn_box" id="template"><div class="devs"><span class="uut_name">uut_name</span>[<span class="uut_status">uut_status</span>]:<span class="rport">rport</span><span class="spi">---></span><span class="hostname">hostname</span>:<span class="lport">lport</span></div><div class="state"><span class="job_template"><span></span><span></span></span></div></div><div id="container"></div></body></html>
"""
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
		page = open("test.html", "r").read()
		return page

	@app.route("/state.json")
	def get_state():
		globals.last_request = time.time()
		if not globals.gatherer:
			globals.gatherer = threading.Thread(target=get_devices_states)
			globals.gatherer.start()
		globals.lock.acquire()
		data = json.dumps(globals.connected_uuts)
		globals.lock.release()
		return data

	app.run(host="0.0.0.0", port=args.port, debug=False)

if __name__ == '__main__':
	run_main(get_parser().parse_args())