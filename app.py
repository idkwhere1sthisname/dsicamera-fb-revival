from __future__ import print_function
from flask import Flask,Response,send_from_directory,abort,render_template,request
from werkzeug.serving import WSGIRequestHandler
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import ssl
import socket
from urllib.parse import unquote
import hashlib as hash
import time
import uuid
import multidict
import colorama
import random
load_dotenv()
app = Flask("fb-integration",template_folder="errors",static_folder="static")
DIR = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(DIR,"static")
CONFIG = os.path.join(DIR,"configuration.xml")
DSI_SECRET = "06807f456ace0a9f505034b1009be9de" # always this
API_KEY = "e8530988ef0ea099f190a9e28a2070c1" # this is also a static value sent by the DSi
UPLOAD_DIR = "uploads"

def dict_dump(passed_dict):
    if isinstance(passed_dict, multidict.MultiDict):
        passed_dict = passed_dict.items(multi=True)

    for key, value in passed_dict.items():
        print(f"{colorama.Fore.CYAN}{key}: {colorama.Fore.YELLOW}{value}{colorama.Style.RESET_ALL}")

def request_dump(request, raw_body=None):
    import colorama
    colorama.init()

    if request.args:
        print(f"{colorama.Fore.MAGENTA}Arguments:{colorama.Style.RESET_ALL}")
        dict_dump(request.args)

    if request.form:
        print(f"{colorama.Fore.MAGENTA}Form items:{colorama.Style.RESET_ALL}")
        dict_dump(request.form)

    print(f"{colorama.Fore.MAGENTA}Headers:{colorama.Style.RESET_ALL}")
    dict_dump(request.headers)

    print(f"{colorama.Fore.MAGENTA}Raw Body:{colorama.Style.RESET_ALL}")
    if raw_body:
        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode("utf-8",errors="replace")
        print(unquote(raw_body))
    else:
        print("(empty)")

def writekey(api_url,ssl_api_url,service,port,usessl="false",filename="key.bin",secret=DSI_SECRET,):
    if usessl == "false":
        prot = "http"
    else:
        prot = "https"
    lines = [
        f"secret:{secret}",
        f"api:{prot}://{api_url}:{port}/restserver.php",
        f"ssl_api:{prot}://{ssl_api_url}:{port}/restserver.php",
        f"use_ssl:{usessl}",
        f"service:{service}"
    ]
    content = b'\n'.join(line.encode('ascii') for line in lines) + b'\n'
    p = os.path.join(STATIC, filename)
    with open(p, "wb") as f:
        f.write(content)
def getlanip():
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    ip = s.getsockname()[0]
    s.close()
    return ip

@app.errorhandler(404)
def notfound(error):
    return render_template("404.html"),404
@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"),403
@app.errorhandler(405)
def methodunallowed(error):
    return render_template("405.html"),405
@app.route("/")
def index():
    return Response("fb",status=200,mimetype="text/html;charset=UTF-8")

@app.route("/fb_files/cert.bin",methods=["GET"])
# not needed (for HTTP, at least), but DSi requests it either way
def servecert():
    crt = os.path.join(STATIC,"cert.bin")
    if not os.path.isfile(crt):
        abort(404)
    return send_from_directory(STATIC,"cert.bin"),200,{"Content-Type":"application/octet-stream"}
@app.route("/fb_files/key.bin",methods=["GET"])
def serveconfig():
    if not os.path.exists(CONFIG):
        return abort(404)
    key = os.path.join(STATIC,"key.bin")
    if not os.path.exists(key):
        return abort(404)
    return send_from_directory(STATIC,"key.bin"),200,{"Content-Type":"application/octet-stream"}

@app.route("/restserver.php", methods=["POST","GET"])
def restserver():
    #for debugging
    # request_dump(request,request.get_data(cache=True,as_text=True))
    data = request.form
    method = unquote(data.get("method", ""))
    rmethod = request.method
    api_key_POST = data.get("api_key",API_KEY)
    v = "1.0"
    payload = '<?xml version="1.0" encoding="utf-8"?>'
    if api_key_POST != API_KEY:
        return abort(403)
    if rmethod != "POST":
        st = 405
        payload += f'<error_msg>invalid request method: {rmethod}</error_msg>'
    else:
        st = 200
        if method == "facebook.auth.createToken":
            rnd = random.randint(0, 2**31 - 1)
            uniq = f"{time.time():.8f}{rnd}"
            tkn = hash.md5(uniq.encode("utf-8")).hexdigest()
            payload += '<auth_createToken_response xmlns="http://api.facebook.com/1.0/">'
            payload += tkn
            payload += '</auth_createToken_response>'
        elif method == "facebook.auth.Login":
            def gensession():
                return str(int(time.time()))
            s = gensession()
            payload += '<auth_login_response xmlns="http://api.facebook.com/1.0/">'
            payload += f'<session_key>SESSION_{s}</session_key>'
            payload += f'<secret>{DSI_SECRET}</secret>'
            payload += f'<uid>91829309382910838393939</uid>' # literally anything
            payload += '<expires>0</expires>'
            payload += '</auth_login_response>'
        elif method == "facebook.auth.grantExtendedPermission":
            payload += '<auth_grantExtendedPermission_response xmlns="http://api.facebook.com/1.0/">'
            payload += '1' # it accepted it, so
            payload += '</auth_grantExtendedPermission_response>'
        elif method == "facebook.auth.expireSession":
            payload += '<auth_expireSession_response xmlns="http://api.facebook.com/1.0/">'
            payload += '1'
            payload += '</auth_expireSession_response>'
        elif method == "facebook.fql.query":
            # since you can't get actual data from facebook's servers, i used fake data
            sig = data.get("sig","")
            query = data.get("query","")
            payload += '<fql_query_response xmlns="http://api.facebook.com/1.0/">'
            payload += '<album>'
            payload += '</album>'
            payload += '</fql_query_response>'
        elif method == "facebook.photos.createAlbum":
            rnd = random.randint(0, 2**31 - 1)
            uniq = f"{time.time():.8f}{rnd}"
            tkn = hash.md5(uniq.encode("utf-8")).hexdigest()
            name_fmt = data.get("name")
            payload += '<photos_createAlbum_response xmlns="http://api.facebook.com/1.0/">'
            payload += f'<aid>{tkn}</aid>'
            payload += f'<name>{name_fmt}</name>'
            payload += f"<size>1</size>"
            payload += "</photos_createAlbum_response>"
        elif method == "facebook.photos.upload":
            if not os.path.exists(UPLOAD_DIR):
                st = 500
                payload += '<error_msg>uploads dir not present</error_msg>'
                return Response(payload,status=st,mimetype="application/xml; charset")
            f = next(iter(request.files.values()),None)
            if not f or f.filename == "":
                print("upload failed")
                st = 500
                payload += "<error_msg>upload failed</error_msg>"
                return Response(payload,status=st,mimetype="application/xml; charset=UTF-8")
            pid = str(uuid.uuid4())
            t = os.path.join(UPLOAD_DIR,f"{pid}.jpg")
            f.save(t)
            print(f"saved image to /uploads/{pid}.jpg");
            aid = data.get("aid","me")
            s = "https" if request.environ.get("wsgi.url_scheme") == "https" else "http"
            host = request.host
            src = f"{s}://{host}/uploads/{pid}.jpg"
            payload += '<photos_upload_response xmlns="http://api.facebook.com/1.0/">'
            payload += f'<pid>{pid}</pid>'
            payload += f'<aid>{aid}</aid>'
            payload += f'<src>{src}</src>'
            payload += '</photos_upload_response>'
        else:
            st = 400
            payload += f'<error_msg>unknown method: {method}</error_msg>'

    return Response(payload,status=st,mimetype="application/xml; charset=UTF-8")

if __name__ == "__main__":
    # set keep-alive
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    try:
        config_file = "configuration.xml"
        if not os.path.exists(config_file):
            host = input("Where should the server run (0.0.0.0 for all interfaces)?: ")
            port = None
            while port is None:
                try:
                    port_input = input("On what port should the server run? (80 is recommended): ")
                    port = int(port_input)
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            port = str(port)
            useSsl = input("Should the server use SSL? (no is recommended) (yes/no): ").lower()
            while useSsl not in ['yes','no']:
                useSsl = input("Please enter either yes or no: ").lower()
            ssl_v = False
            context = None
            if useSsl == "yes":
                print("Please note that SSL/HTTPS on the integration was not tested.")
                input("Please provide your SSL key and certificate (private.key and private.pem), then press enter.")
                if os.path.exists("private.pem") and os.path.exists("private.key"):
                    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                    context.set_ciphers("ALL:@SECLEVEL=0")
                    context.load_cert_chain("private.pem", "private.key")
                    ssl_v = True
                else:
                    print("Couldn't find SSL files. Continuing without SSL...")
            dbg = input("Should the server run in debug mode? (yes/no): ").lower()
            while dbg not in ['yes','no']:
                dbg = input("Please enter either yes or no: ").lower()
            debugmode = dbg == "yes"
            config_xml = ET.Element("config")
            ET.SubElement(config_xml,"host").text = host
            ET.SubElement(config_xml,"port").text = port
            ET.SubElement(config_xml,"ssl").text = str(ssl_v)
            ET.SubElement(config_xml,"debug").text = str(debugmode)
            ET.ElementTree(config_xml).write(config_file, encoding="utf-8", xml_declaration=True)
        else:
            tree = ET.parse(config_file)
            cfg = tree.getroot()
            host = cfg.find("host").text
            port = int(cfg.find("port").text)
            ssl_v = cfg.find("ssl").text.lower() == "true"
            debugmode = cfg.find("debug").text.lower() == "true"
            context = None
            if ssl_v:
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                context.set_ciphers("ALL:@SECLEVEL=0")
                context.load_cert_chain("private.pem", "private.key")
        if not os.path.exists("static/key.bin"):
            status = input("Now, what should the service status be? (anything: makes the service work, ended: shows a shutdown message): ")
            restserverhost = host
            if host == "0.0.0.0":
                restserverhost = getlanip()
            else:
                restserverhost = host
            if status == "ended":
                confirm = input(f'You are setting the service status to "ended", this will disable the integration completely (error code 369000). Are you sure? (yes/no): ')
                while confirm not in ["yes","no"]:
                    confirm = input("Please enter either yes or no: ")
                if confirm == "no":
                    status = "notended"
            writekey(secret=DSI_SECRET,api_url=restserverhost,port=port,ssl_api_url=restserverhost,service=status,filename="key.bin",usessl=str(ssl_v).lower())
        if not os.path.exists("uploads"):
            os.makedirs(UPLOAD_DIR,exist_ok=True)
            print("uploads folder created successfully")
        app.run(host,port,debugmode,ssl_context=context)
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
