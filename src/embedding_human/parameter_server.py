import os
from flask import Flask, render_template, request, jsonify, redirect, views
from ConfigParser import ConfigParser
import time, shutil

#base_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))
tpl_path = os.path.join(base_path, "pages", "template")
static_path = os.path.join(base_path, "pages", 'static')

config_path_base = os.path.join(base_path, "pages", "static", "params.ini")
config_path = os.path.join(base_path, "data", "params.ini")

if not os.path.exists(config_path):
    if os.path.exists(config_path_base) is True:
        shutil.copy(config_path_base, config_path)
    else:
        with open(config_path, "w+") as f:
            f.write("[Default]")
            f.write("[Frequency]")


app = Flask(__name__, template_folder=tpl_path,
            static_folder=static_path, static_url_path="/static")


class ConfigData(object):
    def __init__(self, config_path, section_name="Default", freq_section_name="Frequency", freq=10):
        self.config_path = config_path
        self.config = ConfigParser()
        self.section_name = section_name
        self.freq_section_name = freq_section_name
        self.freq = freq

    def reload(self):
        self.config.read(self.config_path)


    def get(self, key):
        self.reload()
        try:
            return self.config.get(self.section_name, key)
        except:
            return None

    def set(self, key, value):
        self.reload()
        self.config.set(self.section_name, key, value)
        with open(self.config_path, "w+") as f:
            self.config.write(f)
        return True

    @property
    def items(self):
        self.reload()
        items = self.config.items(self.section_name)
        return items

    @property
    def interval(self):
        try:
            self.freq = self.config.get(self.freq_section_name, "interval")
        except Exception as e:
            print(e)
        return self.freq

    @interval.setter
    def interval(self, value):
        if not value.isdigit():
            pass
        else:
            self.reload()
            _freq = int(value)
            if self.freq != _freq:
                self.freq = _freq
                self.config.set(self.freq_section_name, "interval", self.freq)
                with open(self.config_path, "w+") as f:
                    self.config.write(f)
                print("update interval change to", self.freq)
        return True


config = ConfigData(config_path)


@app.route("/parameters", methods=["GET", "POST"])
def parameters():
    if request.method == "POST":
        datas = request.form
        for d in datas:
            if d == "_interval":
                config.interval = datas[d]
            else:
                config.set(d, datas[d])
        return redirect("/parameters")
    context = {"items": config.items, "interval": config.interval}
    return render_template("parameters.html", datas=context)


@app.route("/api/parameters", methods=["GET"])
def parameters_api():
    keys = config.items
    keys = {k:v for k,v in keys}
    keys["_interval"] = config.interval
    return jsonify(keys)

face_list = list()

class RecognizeFace(views.MethodView):
    def get(self):
        global face_list
        try:
            item = face_list[0]
            if time.time() - float(item.get("recognized_time")) < 30:
                return jsonify(item)
        except Exception as e:
            print(e)
        finally:
            face_list = list()
        return jsonify({})

    def post(self):
        global face_list
        data = request.form.to_dict()
        face_list.append(data)
        face_list.sort(key=lambda x: x.get("recognized_time"), reverse=True)
        if len(face_list) > 10:
            face_list.pop()
        return jsonify({"status": "ok"})

app.add_url_rule("/api/recognizeFace/", view_func=RecognizeFace.as_view(name="recognizeFace"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
    # app.run(host="0.0.0.0")
