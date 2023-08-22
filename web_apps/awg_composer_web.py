#!/usr/bin/env python3

import argparse
import os
import re

import bottle
from bottle import route, run, response, request, static_file
import waves.build_templates as build_templates

def run_main(args):
    print('run main')
    web_server(args)

def web_server(args):
    """
        / - index
        /endpoint - json endpoint
        /manifest - current manifest 
    """
    @route('/')
    def handle_root():
        response.content_type = 'text/html'
        return root_html
    
    @route('/endpoint', method='POST')
    def handle_endpoint():
        result = False
        msg = 'NULL'
        data = request.json
        print(data)
        if not data or 'action' not in data:
            response.status = 405
            response.body = 'Bad Json'
            print('Bad Json')
            return response
        
        action = data['action']
        
        if action == 'build_template':
            result, msg = handle_build_template(data['lines'])
            print(result)
            print(msg)

        if action == 'awg_compose':
            result, msg = handle_run_composer(data['filename'], data['cmd_args'])
            print(result)
            print(msg)

        code = 200 if result else 400
        response.status = code
        response.body = msg

        return response
    
    @route('/manifest')
    def handle_manifest():
        return static_file('MANIFEST', root='/tmp/AWG', mimetype='text/plain')
    
    run(host='0.0.0.0', port=args.web_port, quiet=False)

def handle_build_template(lines):
    return build_templates.from_array(lines)

def handle_run_composer(filename, cmd_args):
    filename = escape_input(filename)
    cmd_args = escape_input(cmd_args)
    cmd = f"/mnt/local/awg_composer -o /tmp/{filename}.dat {cmd_args}"
    return_value = os.system(cmd)
    if return_value > 0:
        return False, f"Compose Failure {cmd}"
    return True, f"Compose success {cmd}"

def escape_input(user_input):
    periods_colons_slashes = r"[.;:\/]*"
    return re.sub(periods_colons_slashes, '', user_input)

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
        .box .title{
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

        #manifest_contents{
            background-color: var(--code_grey);
            padding: 5px;
            border: 2px solid transparent
        }
        .cmd_input{
            background-color: var(--code_grey);
            padding: 10px 20px;
            margin: 0;
            border: 2px solid transparent;
        }
        .cmd_input span{
            outline: none;
            border: none;
            background-color: #fff;
            min-width: 20px;
            display: inline-block;
            border-bottom: 1px solid var(--accent);
            -webkit-box-sizing: border-box;
                    box-sizing: border-box;
            word-break: break-all;
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
        .response_good{
            -webkit-animation-name: to_green;
                    animation-name: to_green;
            -webkit-animation-duration: 5s;
                    animation-duration: 5s;
        }
        .response_bad{
            -webkit-animation-name: to_red;
                    animation-name: to_red;
            -webkit-animation-duration: 5s;
                    animation-duration: 5s;
        }
        @-webkit-keyframes to_green {
            0% {}
            5% {border-color: var(--success)}
            100% {border-color: var(--success)}
        }
        @keyframes to_green {
            0% {}
            5% {border-color: var(--success)}
            100% {border-color: var(--success)}
        }
        @-webkit-keyframes to_red {
            0% {}
            5% {border-color: var(--failure)}
            100% {border-color: var(--failure)}
        }
        @keyframes to_red {
            0% {}
            5% {border-color: var(--failure)}
            100% {border-color: var(--failure)}
        }
    </style>
    <script>
        const url_base = new URL(window.location.pathname, window.location.origin);
        function upload_lines(e){
            file = e.target.files[0];
            const reader = new FileReader();
            reader.addEventListener("load", () => {
                let payload = {
                    'action' : 'build_template',
                    'lines' : reader.result.split("\\n")
                }
                let url = new URL(`${url_base.href}endpoint`);
                var manifest_contents = document.getElementById('manifest_contents');
                manifest_contents.classList = '';
                send_request(url.toString(), 'POST', (code, response) => {
                    e.target.value = null;
                    if(code >= 200 && code < 300){
                        manifest_contents.classList.add('response_good');
                        update_manifest();
                        console.log('upload_lines succeded');
                        return
                    }
                    console.log('upload_lines failed');
                    alert(response);
                }, JSON.stringify(payload));
            });
            if(file.type != 'text/plain'){
                alert(`Invalid filetype`);
                return
            }
            reader.readAsText(file);
        }
        function update_manifest(){
            let url = new URL(`${url_base.href}manifest`);
            var manifest_contents = document.getElementById('manifest_contents');
            send_request(url.toString(), 'GET', function (code, response){
                manifest_contents.innerText = response;
            });
        }
        function send_compose(e){
            cmd_input = e.target.parentNode.querySelector('.cmd_input');
            filename = document.querySelector('#filename_input').innerText;
            cmd_args = document.querySelector('#args_input').innerText;
            cmd_input.classList = 'cmd_input';
            let payload = {
                'action' : 'awg_compose',
                'filename' : filename,
                'cmd_args' : cmd_args
            }
            let url = new URL(`${url_base.href}endpoint`);
            send_request(url.toString(), 'POST', (code, response) => {
                if(code >= 200 && code < 300){
                    cmd_input.classList.add('response_good');
                    return;
                }
                cmd_input.classList.add('response_bad');
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
        window.onload = ()=>{
            console.log('Page Loaded');
            document.querySelector('#upload_input').addEventListener('change', (e) => {
                upload_lines(e);
            }, false);
            document.querySelector('#compose_input').addEventListener('click', (e) => {
                send_compose(e);
            }, false);
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
                        <h3>Choose or drop file</h3>
                        <input type="file" id="upload_input" />
                    </div>
                </div>
            </div>
            <div class="box">
                <h2 class="title">:Compose</h2>
                <div class="contents">
                    <h4 class="cmd_input">/mnt/local/awg_composer -o /tmp/<span id="filename_input" role="textbox" contenteditable>flash_scan</span>.dat <span id="args_input" role="textbox" contenteditable>5*AA 5*BB</span></h4>
                    <button id="compose_input">Compose</button>
                </div>
            </div>

            <div class="box">
                <h2 class="title">:Manifest</h2>
                <div class="contents">
                    <div id="manifest_contents"></div>
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