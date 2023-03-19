from mr_graph.node_data_class import NodeDataClass

class NodeDataTracker:
    fields: list[str]
    field_map: dict[str,str]

    def __init__(self, output_to_track:NodeDataClass):
        self.fields = list()
        self.field_map = dict()
        self.data_class = output_to_track
        node_name = getattr(output_to_track, '__node_name')
        for key, value in output_to_track.__dict__.items():
            if key != '__node_name':
                graph_tracking_tuple = ('mr_graph_node', node_name, key)
                setattr(self, key, graph_tracking_tuple)
                self.fields.append(key)
            else:
                setattr(self, key, value)
    
    def __iadd__(self, other):
        for key in other.fields:
            if key in self.fields:
                raise Exception(f'adding two NodeDataTracker with the same field: {key}')
            setattr(self, key, key)
            self.fields.append(key)
            self.field_map[getattr(other, '__node_name')] = key
        if getattr(other, '__node_name') !=  getattr(self, '__node_name'):
            setattr(self, '__node_name', 'composite_node')
        return self
