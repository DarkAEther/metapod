from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
from flask_bcrypt import Bcrypt

import docker
import inspect
import pprint

app = Flask(__name__)
api = Api(app)
bcrypt = Bcrypt(app)

def get_necess_data(data, necess_attrs):
    return {
            i: (
                {j: data[i][j] for j in necess_attrs[i] if j in data[i]} 
                if necess_attrs[i] 
                else data[i]
            ) for i in necess_attrs if i in data
        }

class Register(Resource):
    def post(self):
        cluster = MongoClient("mongodb+srv://admin:admin123@cluster0.ceaix.mongodb.net/metapod?retryWrites=true&w=majority")

        db = cluster["metapod"]
        collection = db["users"]
        
        email = request.json['email']
        password = request.json['password']

        if(collection.find_one({'email': email}) is None):
            hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')

            entry = {
                    "email" : email,
                    "password" : hashed_pwd 
                }

            collection.insert_one(entry)

            return {'result': "user registered"}   
        else:
            return {'result': "user already exists"}

class Login(Resource):
    def post(self):
        cluster = MongoClient("mongodb+srv://admin:admin123@cluster0.ceaix.mongodb.net/metapod?retryWrites=true&w=majority")

        db = cluster["metapod"]
        collection = db["users"]

        email = request.json['email']
        password = request.json['password']

        entry = collection.find_one({'email': email})
        
        if(entry is not None):
            result = bcrypt.check_password_hash(entry['password'], password)

            if(result == True):
                return {'result': "user authenticated"}
            else:
                return {'result': "invalid credentials"}

        else:
            return {'result': "user not found"}        


class Containers(Resource):
    def get(self):
        #CONTAINER ID   IMAGE     COMMAND                  CREATED       STATUS                   PORTS     NAMES
        #598079914e20   nginx     "/docker-entrypoint.…"   3 hours ago   Exited (0) 3 hours ago             zen_cerf

        cluster = MongoClient("mongodb+srv://admin:admin123@cluster0.ceaix.mongodb.net/metapod?retryWrites=true&w=majority")

        db = cluster["metapod"]
        collection = db["containers"]

        if(collection.count_documents({}) != 0):
            collection.delete_many({})

        client = docker.from_env()

        for c in client.containers.list(all = True):
            entry = {
                'ContainerId': c.short_id,
                'Image': c.attrs['Config']['Image'],
                'Command': c.attrs['Path'],
                'Created': c.attrs['Created'],
                'Status': c.status + ' (' + str(c.attrs['State']['ExitCode']) + ') at ' + c.attrs['State']['FinishedAt'],
                'Ports': c.ports,
                'Name': c.name
            }

            collection.insert_one(entry)

        allContainers = []
        for doc in collection.find({}):
            doc.pop('_id')
            allContainers.append(doc)

        return {'containers' : allContainers}, 200

class Container(Resource):
    def get(self,id_or_name):
        client = docker.from_env()
        cont = client.containers.get(id_or_name)

        necess_attrs = {
            'AppArmorProfile': [],
            'Config': ['Cmd', 'Entrypoint', 'ExposedPorts', 'Hostname', 'Image', 'User', 'Volumes', 'WorkingDir'],
            'Created': [],
            'HostConfig': ['CapAdd', 'CapDrop', 'Cgroup', 'CgroupParent', 'CpuCount', 'CpuShares', 'CpusetCpus', 'CpusetMems', 'DeviceCgroupRules', 'Devices', 'IOMaximumBandwidth', 'IOMaximumIOps', 'IpcMode', 'MaskedPaths', 'Memory', 'MemoryReservation', 'NanoCpus', 'NetworkMode', 'PortBindings', 'Privileged', 'PublishAllPorts', 'ReadonlyPaths', 'ReadonlyRootfs'],
            'Id': [],
            'Image': [],
            'Mounts': [],
            'Name': [],
            'NetworkSettings': [],
            'State': []
        }

        return get_necess_data(cont.attrs, necess_attrs), 200

class Images(Resource):
    def get(self):
        #REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
        #ubuntu       latest    f63181f19b2f   2 weeks ago   72.9MB

        cluster = MongoClient("mongodb+srv://admin:admin123@cluster0.ceaix.mongodb.net/metapod?retryWrites=true&w=majority")

        db = cluster["metapod"]
        collection = db["images"]

        if(collection.count_documents({}) != 0):
            collection.delete_many({})

        client = docker.from_env()

        for i in client.images.list(all = True):
            entry = {
                'Repository': i.tags[0].split(':')[0] if i.tags else '',
                'Tag': i.tags[0].split(':')[1] if i.tags else '',
                'ImageId': i.short_id.split(':')[1],
                'Created': i.attrs['Created'],
                'Size': round(i.attrs['Size'] / 1000000, 1)
            }

            collection.insert_one(entry)

        allImages = []
        for doc in collection.find({}):
            doc.pop('_id')
            allImages.append(doc)

        return {'images' : allImages}, 200

class Image(Resource):
    def get(self,id_or_name):
        client = docker.from_env()
        img = client.images.get(id_or_name)

        # print('\n\n\n\n\n')
        # for i in inspect.getmembers(img):
        #     if not i[0].startswith('_'):
        #         if not inspect.ismethod(i[1]):  
        #             pprint.pprint(i) 
        # print('\n\n\n\n\n')

        necess_attrs = {
            'Author': [],
            'Config': ['Cmd', 'Entrypoint', 'Env', 'Hostname', 'Image'],
            'Created': [],
            'Id': [],
            'RepoTags': [],
            'Size': [],
            'VirtualSize': []
        }

        return get_necess_data(img.attrs, necess_attrs), 200

api.add_resource(Containers, '/api/v1/containers')
api.add_resource(Container, '/api/v1/containers/<string:id_or_name>')
api.add_resource(Images, '/api/v1/images')
api.add_resource(Image, '/api/v1/images/<string:id_or_name>')
api.add_resource(Register, '/api/v1/register')
api.add_resource(Login, '/api/v1/login')

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=80, debug=True)
