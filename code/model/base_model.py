import tensorflow as tf
_MODEL_NAME = []

class BaseModel(object):
    '''
    Base model for all models
    '''
    def __init__(self, 
                 hidden_num, hidden_dim,
                 input_dim, output_dim,
                 name):
        '''
        Create model
        '''
        # Each model should have a unique name in one run
        if name in _MODEL_NAME:
            print('Model name: ', name, 'is used.')
            exit()
    
        self.name = name

        #A list of layers in the model
        self.layers = []
        #The number of hidded layers
        #The first layer is the input layer, the last layer is the output layer
        #So, hidden_num = len(layers) - 1
        self.hidden_num = hidden_num
        #The dimension of hidded layers' output
        #The first element is input_dim, the last element is output_dim
        self.hidden_dim = hidden_dim
        self.hidden_dim = [input_dim] + self.hidden_dim
        self.hidden_dim.append(self.output_dim)

        #This is a list of outputs of each layers
        self.activations = []

        self.inputs = None
        self.outputs = None

        self.loss = 0

        self.optimizer = None


    def _add_layers(self):
        '''
        Create layers
        It should be defined in the speicfic model class
        '''
        raise NotImplementedError

    def _loss(self):
        '''
        Loss function, not defined here
        It should be defined in the specific model class
        '''
        raise NotImplementedError
    
    def build(self):
        '''
        Build models
        '''
        
        # Create layers, in variable scope: name
        with tf.variable_scope(self.name):
            self._add_layers()
        
        # Connect inputs and layers
        self.activations.append(input)
        for each_layer in self.layers:
            #The input is the output of the previous layer
            act = layer(self.activation[-1])
            self.activations.append(act)
        #output is the last layer's output
        self.outputs = self.activations[-1]
        
        

        variables = tf.get_collection(tf.GraphKeys)

        loss = _loss()

    def train(self,)
    	pass
    
    def draw_graph(self, path, file_name):
        '''
        Use tensorboard to draw the graph
        '''        


    
    



