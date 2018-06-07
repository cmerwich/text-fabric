import rpyc
from rpyc.utils.server import ThreadedServer

from tf.fabric import Fabric


def makeTfServer(locations, modules, port):
    print(f'Setting up Text-Fabric service for {locations} / {modules}')
    TF = Fabric(locations=locations, modules=modules, silent=False)
    api = TF.load('', silent=True)
    allFeatures = TF.explore(silent=True, show=True)
    loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
    TF.load(loadableFeatures, add=True, silent=False)
    print(f'Listening at port {port}')

    class TfService(rpyc.Service):
        def on_connect(self):
            self.api = api
            pass

        def on_disconnect(self):
            self.api = None
            pass

        def exposed_search(self, query, context):
            api = self.api
            S = api.S
            return S.search(query, withContext=context)

    return ThreadedServer(TfService, port=port)


def makeTfConnection(host, port):
    class TfConnection(object):
        def connect(self):
            connection = rpyc.connect(host, port)
            self.connection = connection
            return connection.root

    return TfConnection()
