#!/usr/bin/env python3

import argparse
import os
import re

from bottle import route, run, response, request, static_file
import waves.build_templates as build_templates
import threading

"""
Usage:
    ./web_apps/awg_composer_web.py --web_port=5000
    (&>/dev/null ./web_apps/awg_composer_web.py &)
"""

class globals:
    compose_status = (False, None)
    root_dir = '/tmp/AWG/'

def run_main(args):
    print('run main')
    web_server(args)

def web_server(args):
    print('Starting webserver')
    @route('/')
    def handle_root():
        #return static_file('temp.html', root='web_apps/') # testing
        response.content_type = 'text/html'
        return root_html
    
    @route('/endpoint', method='POST')
    def handle_endpoint():
        result = False
        action_map = {
            'build_template': handle_build_template,
            'awg_compose': handle_run_composer,
            'erase_templates': handle_erase_templates,
        }

        try:
            action = action_map[request.json['action']]
            data = request.json['data']
            result, body = action(**data)
        except Exception as e:
            body = f"Error {e}"

        code = 200 if result else 400
        response.status = code
        response.body = body

        return response
    
    @route('/manifest')
    def handle_manifest():
        manifest = get_manifest()
        if manifest:
            response.content_type = 'text/plain'
            return manifest
        response.status = 404
        return 'None'
    
    @route('/compose_status')
    def handle_composing():
        return {'compose_status': globals.compose_status}
    
    run(host='0.0.0.0', port=args.web_port, quiet=True)

def handle_build_template(lines, **kwargs):
    print("Building Template")
    return build_templates.from_array(lines)

def handle_run_composer(output, pattern, nrep='', **kwargs):
    if globals.compose_status[0]:
        return False, f"Compose Running"
    if not get_manifest():
        return False, f"No Manifest"
    
    awg_outputs = ['oneshot_rearm', 'oneshot', 'continuous']

    if output in awg_outputs:
        output = f"--awg_mode {output}"
    else:
        output = f"-o /tmp/{escape_input(output)}"
    if nrep:
        nrep = f"--nreps {escape_input(nrep)}"

    pattern = escape_input(pattern)
    cmd = f"/mnt/local/awg_composer {output} {nrep} {pattern}"
    threading.Thread(target=run_compose, args=(cmd,)).start()
    return True, f"Compose started {cmd}"

def handle_erase_templates(**kwargs):
    os.system(f"rm -rf {globals.root_dir}")
    return True, 'templates erased'

def run_compose(cmd):
    globals.compose_status = (True, 'Composing')
    print(f"[COMPOSER] Running {cmd}")
    return_code = os.system(cmd)
    print(f"[COMPOSER] Finished")
    if return_code > 0:
        print(f"Errored {return_code}")
        globals.compose_status = (False, 'Errored')
        return
    globals.compose_status = (False, 'Done')

def escape_input(user_input):
    colons_slashes = r"[;:\/]*"
    return re.sub(colons_slashes, '', user_input)

def get_manifest():
    filepath = '/tmp/AWG/MANIFEST'
    if not os.path.isfile(filepath) :
        return False
    with open(filepath) as f:
       return f.read()

def get_parser():
    parser = argparse.ArgumentParser(description='awg_composer_web')
    parser.add_argument('--web_port', default=5000, help="webserver port")
    return parser

root_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        html, body{
            height: 100%;
            width: 100%;
        }
        body{
            font-family: "Courier New", Courier, monospace;
            margin: 0;
        }
        :root {
            --accent: #002AFF;
            --code_grey: #F6F6F6;
            --main_background: antiquewhite;
            --success: #2ecc71;
            --failure: #e74c3c;
        }
        .wrapper{
            height: 100%;
            -webkit-box-orient: vertical;
            -webkit-box-direction: normal;
                -ms-flex-direction: column;
                    flex-direction: column;
            display: -webkit-box;
            display: -ms-flexbox;
            display: flex;
            -webkit-box-sizing: border-box;
                    box-sizing: border-box;
        }
        .overlay{
            display: none;
        }
        .header{
            border-bottom: 2px solid var(--accent);
        }
        .header .title{
            word-break: break-all;
        }
        .main{
            display: block;
            background-color: var(--main_background);
            -webkit-box-flex: 1;
                -ms-flex-positive: 1;
                    flex-grow: 1;
            padding: 10px 0px;
        }
        .footer{
            background-color: var(--accent);
            color: #fff;
            padding: 10px;
        }
        .header, .main, .footer{
            max-width: 100%;
            padding-left: 5%;
            padding-right: 5%;
        }
        .box{
            border: 2px solid black;
            outline: 2px solid grey;
            background-color: #fff;
            display: inline-block;
            vertical-align: top;
            margin-top: 20px;
        }
        .box > .title{
            background-color: #fff;
            margin: 0;
            border-bottom: 2px solid black;
            padding: 10px 5px;
        }
        .box .contents{
            padding: 10px;
        }
        .drop_area{
            width: 300px;
            height: 300px;
            border: 4px dashed black;
            background-color: #fff;
            overflow: hidden;
            position: relative;
            text-align: center;
            display: inline-block;
            vertical-align: top;
        }
        .drop_area input{
            width: 200%;
            height: 100%;
            margin-left: -100%;
            z-index: 999;
            position: absolute;
            left: 0;
            top: 0;
            cursor: pointer;
        }
        .drop_area h3{
            position: absolute;
            top: 50%;
            left: 50%;
            -webkit-transform: translate(-50%, -50%);
                -ms-transform: translate(-50%, -50%);
                    transform: translate(-50%, -50%);
            width: 100%;
            margin: 0;
            -webkit-user-select: none;
            -moz-user-select: none;
                -ms-user-select: none;
                    user-select: none;
        }
        .drop_area:hover{
            border-color: var(--accent);
            color: var(--accent);
        }
        .compose_option{
            padding: 10px 0px;
            display: inline-block;
        }
        .compose_option h3{
            margin: 0;
            margin-bottom: 10px;
        }
        .compose_option span{
            width: 100px;
            display: inline-block;
            text-align: right;
        }
        .live_option{
            appearance: none;
            outline: none;
            border: 0px;
            font-size: 1rem;
            border-bottom: 1px solid var(--accent);
            min-width: 250px;
            box-sizing: border-box;
        }
        .med_button{
            cursor: pointer;
            border: none;
            font-weight: bold;
            color: #fff;
            padding: 10px 20px;
            background-color: var(--accent);
            margin-top: 10px;   
        }
        .cmd_input{
            background-color: var(--code_grey);
            padding: 10px 20px;
            margin: 0;
            border: 2px solid transparent;
        }
        .cmd_input span{
            display: inline-block;
        }
        #compose_input{
            cursor: pointer;
            border: none;
            font-weight: bold;
            color: #fff;
            padding: 10px 20px;
            background-color: var(--accent);
            margin-top: 10px;   
        }
        #compose_status{
            padding: 5px 10px;
        }
        #manifest_contents{
            background-color: var(--code_grey);
            padding: 5px;
            border: 2px solid transparent
        }
        #template_erase{
            display: none;
        }
        .has_manifest + #template_erase{
            display: block;
        }
        .update_elem{
            -webkit-animation-name: update;
                    animation-name: update;
            -webkit-animation-duration: 2s;
                    animation-duration: 2s;
        }
        @keyframes update {
            0% {}
            5% {color: var(--accent)}
            5% {color: var(--accent)}
        }
        @-webkit-keyframes update {
            0% {}
            5% {color: var(--accent)}
            5% {color: var(--accent)}
        }
    </style>
    <script>
        const url_base = new URL(window.location.pathname, window.location.origin);
        function upload_lines(e){
            const NEWLINE = '\\n';
            file = e.target.files[0];
            const reader = new FileReader();
            reader.addEventListener("load", () => {
                let payload = {
                    'action' : 'build_template',
                    'data': {
                        'lines' : reader.result.split(NEWLINE)
                    }
                }
                let url = new URL(`${url_base.href}endpoint`);
                send_request(url.toString(), 'POST', (code, response) => {
                    e.target.value = null;
                    if(code >= 200 && code < 300){
                        update_manifest();
                        console.log('upload_lines succeded');
                        return;
                    }
                    console.log('upload_lines failed');
                    alert(response);
                }, JSON.stringify(payload));
            });
            if(file.type != 'text/plain'){
                alert(`Invalid filetype`);
                return;
            }
            reader.readAsText(file);
        }
        function erase_templates(e){
            let payload = {
                'action' : 'erase_templates',
                'data' : {}
            }
            let url = new URL(`${url_base.href}endpoint`);
            send_request(url.toString(), 'POST', (code, response) => {
                update_manifest();
            }, JSON.stringify(payload));
        }
        function update_manifest(){
            let url = new URL(`${url_base.href}manifest`);
            var manifest_contents = document.getElementById('manifest_contents');
            manifest_contents.classList = '';
            send_request(url.toString(), 'GET', function (code, response){
                manifest_contents.innerText = response;
                if(code >= 400){
                    manifest_contents.classList = 'update_elem';
                    return;
                }
                manifest_contents.classList = 'update_elem has_manifest';
            });
        }
        function send_compose(e){
            compose_status = document.querySelector('#compose_status');
            cmd_input = e.target.parentNode.querySelector('.cmd_input');
            output = document.querySelector('#compose_output').dataset.value;
            pattern = document.querySelector('#compose_pattern').dataset.value;
            nrep = document.querySelector('#compose_nrep').dataset.value;
            cmd_input.classList = 'cmd_input';
            let payload = {
                'action' : 'awg_compose',
                'data' : {
                    'output' : output,
                    'pattern' : pattern,
                    'nrep' : nrep
                }
            }
            let url = new URL(`${url_base.href}endpoint`);
            function poll_until_complete(){
                let url = new URL(`${url_base.href}compose_status`);
                compose_status.classList = '';
                send_request(url.toString(), 'GET', function (code, response){
                    var [composing, status] = JSON.parse(response)['compose_status'];
                    compose_status.innerText = status;
                    compose_status.classList = 'update_elem';
                    if(!composing){
                        return
                    }
                    setTimeout(poll_until_complete, 1000); 
                });
            }
            send_request(url.toString(), 'POST', (code, response) => {
                if(code >= 200 && code < 300){
                    poll_until_complete();
                    return;
                }
                alert(response);
            }, JSON.stringify(payload));
        }
        function send_request(url, method, callback, payload = null){
            var xhr = new XMLHttpRequest();
            xhr.open(method, url, true);
            xhr.onreadystatechange = function() {
                if(xhr.readyState == 4) {
                    callback(xhr.status, xhr.response);
                }
            }
            if(payload){
                xhr.setRequestHeader('Content-Type', 'application/json');
            }
            xhr.send(payload);
        }
        function live_updater(e){
            elem = e.target;
            value = elem.value;
            pre = elem.dataset.pre ? elem.dataset.pre : '';
            if(elem.tagName == 'SELECT'){
                option = elem.options[elem.selectedIndex];
                pre = option.dataset.pre ? option.dataset.pre : '';
            }
            target_elem = document.getElementById(elem.dataset.target);
            target_elem.innerText = `${pre}${value}`;
            target_elem.dataset.value = value;
            if(value.length == 0){
                target_elem.innerText = '';
                target_elem.dataset.value = '';
            }
        }
        window.onload = ()=>{
            console.log('Page Loaded');
            document.querySelector('#upload_input').addEventListener('change', (e) => {
                upload_lines(e);
            }, false);
            document.querySelector('#compose_input').addEventListener('click', (e) => {
                send_compose(e);
            }, false);
            document.querySelector('#template_erase').addEventListener('click', (e) => {
                erase_templates(e);
            }, false);
            document.querySelectorAll(".live_option").forEach((elem) => {
                elem.addEventListener('input', (e) => {
                    live_updater(e);
                }, false);
            });
            update_manifest();
        }
        </script>
</head>
<body>
    <div class="wrapper">
        <div class="header">
            <h1 class="title">AWG Composer Web</h1>
        </div>
        <div class="main">
            <div class="box">
                <h2 class="title">:Upload</h2>
                <div class="contents">
                    <div class="drop_area">
                        <h3>Click or drop file</h3>
                        <input type="file" id="upload_input" />
                    </div>
                </div>
            </div>
            <div class="box">
                <h2 class="title">:Compose</h2>
                <div class="contents">
                    <div class="compose_option">
                        <span>Output: </span>
                        <select class="live_option" data-target="compose_output">
                            <option data-pre="--awg_mode  ">oneshot_rearm</option>
                            <option data-pre="--awg_mode ">oneshot</option>
                            <option data-pre="--awg_mode ">continuous</option>
                            <option data-pre="-o /tmp/">composed.dat</option>
                        </select><br>
                        <span>Pattern: </span>
                        <input class="live_option" data-target="compose_pattern" type="text" value="5*AA 5*BB" autocomplete="off"><br>
                        <span>Nrep: </span>
                        <input class="live_option" data-target="compose_nrep" type="number" data-pre="--nreps " autocomplete="off"><br>
                    </div>
                    <h4 class="cmd_input">
                        <span>/mnt/local/awg_composer</span> 
                        <span id="compose_output" data-value="oneshot_rearm">--awg_mode oneshot_rearm</span> 
                        <span id="compose_nrep" data-value=""></span> 
                        <span id="compose_pattern" data-value="5*AA 5*BB">5*AA 5*BB</span> 
                    </h4>
                    <button id="compose_input" class="med_button">Compose</button>
                    <span id="compose_status"></span>
                </div>
            </div>
            <div class="box">
                <h2 class="title">:Manifest</h2>
                <div class="contents">
                    <div id="manifest_contents">None</div>
                    <button id="template_erase" class="med_button">Erase</button>
                </div>
            </div>
        </div>
        <div class="footer">
            dtacq 2023
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    run_main(get_parser().parse_args())