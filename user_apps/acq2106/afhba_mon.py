#!/usr/bin/env python3

import argparse
import os
from flask import Flask
import threading
import time
import json
import acq400_hapi
from acq400_hapi import afhba404


class globals:
	lock = threading.RLock()
	devices = {}
	uuts = {}
	threads = {}
	gatherer = None
	last_request = 0
	last_ident = 0
	hostname = None

def get_parser():
	parser = argparse.ArgumentParser(description='Stream monitor webserver')
	parser.add_argument('--port', default=5000, help='Port to run webserver on')
	return parser

def run_main(args):
	globals.hostname = os.uname()[1]
	run_webserver(args)

def get_devices_states():
	while True:
		print("Getting states")
		if time.time() - globals.last_ident > 60:
			globals.last_ident = time.time()
			globals.threads['ident'] = threading.Thread(target=get_devices)
			globals.threads['ident'].start()
		globals.lock.acquire()
		for dev in globals.devices.items():
			dev[1]['job_state'] = afhba404.get_stream_state(dev[1]['lport'])._asdict()
			globals.threads[dev[0]] = threading.Thread(target=get_remote_state,  args=(dev[0],))
			globals.threads[dev[0]].start()
		globals.lock.release()
		if time.time() - globals.last_request > 60:
			print('Thread idle killing self')
			globals.gatherer = None
			exit()
		time.sleep(1)

def get_devices():
	devs = afhba404.get_connections()
	print("Getting connected uuts")
	globals.lock.acquire()
	for dev in devs.items():
		if dev[1].uut not in globals.devices:
			globals.devices[dev[1].uut] = {}
			globals.devices[dev[1].uut]['job_state'] = {}
			globals.devices[dev[1].uut]['uut_status'] = None
			globals.devices[dev[1].uut]['rport'] = dev[1].cx
			globals.devices[dev[1].uut]['lport'] = dev[1].dev
			globals.devices[dev[1].uut]['hostname'] = globals.hostname
		if dev[1].uut not in globals.uuts:
			try:
				globals.uuts[dev[1].uut] = acq400_hapi.factory(dev[1].uut)
			except Exception as e:
				print(e)
	globals.lock.release()

def get_remote_state(name):
	uut_state = globals.uuts[name].s0.CONTINUOUS_STATE
	globals.lock.acquire()
	globals.devices[name]['uut_status'] = uut_state.split()[1]
	globals.lock.release()
	exit()

page = """
<!DOCTYPE html><html lang="en"><head><meta name="google" value="notranslate"><title>afhba monitor</title><style>body{background-color:#e8e9f3;font-family:"Courier New",Courier,monospace}
#template{display:none}.IDLE{color:red}.RUN{color:#adff2f}.ARM{color:orange}.conn_box{background-color:#8395a7;font-size:16px;margin-bottom:10px;overflow:auto}
.devs{font-size:20px;margin-bottom:0;padding:5px 10px;display:flex}.spi{padding:0 10px;color:orange}.state{background-color:#c8d6e5;margin:5px 5px;padding:2px}</style>
<script>function main(){url="state.json","hidden"!=document.visibilityState&&get_state(url,callback),setTimeout(main,1e3)}
function get_state(e,t){var n=new XMLHttpRequest;n.open("GET",e,!0),n.responseType="json",n.onreadystatechange=function(){4==n.readyState&&200==n.status&&t(n.response)},n.send()}
function callback(e){for(let[t,n]of(template=document.getElementById("template"),(container=document.getElementById("container")).innerHTML="",Object.entries(e))){for(let[s,a]of((
new_row=template.cloneNode(!0)).id="",new_row.getElementsByClassName("uut_name")[0].innerText=t,new_row.getElementsByClassName("uut_status")[0].innerText=n.uut_status,
new_row.getElementsByClassName("uut_status")[0].className=n.uut_status,new_row.getElementsByClassName("rport")[0].innerText=n.rport,new_row.getElementsByClassName("hostname")[0].innerText=location.hostname,
new_row.getElementsByClassName("lport")[0].innerText=n.lport,state="",Object.entries(n.job_state)))state+=`${s}=${a} `;
new_row.getElementsByClassName("state")[0].innerText=state,container.appendChild(new_row)}}window.onload=main();</script></head><body><h1>afhba monitor</h1><div class="conn_box" id="template">
<div class="devs"><span class="uut_name">uut_name</span>[<span class="uut_status">uut_status</span>]:<span class="rport">rport</span><span class="spi">---></span><span class="hostname">hostname</span>:
<span class="lport">lport</span></div><div class="state">job_state</div></div><div id="container"></div></body></html>
"""
def run_webserver(args):
	app = Flask(__name__,)

	@app.route("/")
	def get_index():
		globals.last_ident = 0
		if not globals.gatherer:
			globals.gatherer = threading.Thread(target=get_devices_states)
			globals.gatherer.start()
		return page

	@app.route("/state.json")
	def get_state():
		globals.last_request = time.time()
		if not globals.gatherer:
			globals.gatherer = threading.Thread(target=get_devices_states)
			globals.gatherer.start()
		globals.lock.acquire()
		data = json.dumps(globals.devices)
		globals.lock.release()
		return data

	app.run(host="0.0.0.0", port=args.port)

if __name__ == '__main__':
	run_main(get_parser().parse_args())