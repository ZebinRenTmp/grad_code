import tensorflow as tf
import scipy.sparse as sp
from .layer_utils import *

class BaseLayer(object):
    def __init__(self,
                 input_dim, output_dim,
                 activation_func,
                 name,
                 dropout_prob = None,
                 bias = False,
                 sparse = False
                 ):
        #Initialize some variables
        self.name = name
        self.activation_func = activation_func
        self.dropout_prob = dropout_prob
        self.bias = bias
        self.sparse = sparse
        self.weight_decay_vars = []

        self.input_dim = input_dim
        self.output_dim = output_dim


        #If dropout_prob is assigned a value
        if self.dropout_prob:
            #Check if the type of dropout_prob is legal
            if type(self.dropout_prob) is type(1.0):
                pass
            else:
                print("droupout_prob is: ", self.dropout_prob)
                raise Exception('Invalid type for dropout.')

            #Check if the value is legal
            if 0.0 < self.dropout_prob < 1.0:
                pass
            else:
                print("droupout_prob is: ", self.dropout_prob)
                raise Exception('Invalid value for droupout.')
            

    #This function is invocked by the object name
    def __call__(self, inputs, num_features_nonzero):
        with tf.name_scope(self.name):   
            return self.run(inputs, num_features_nonzero)
    
    def run(self, inputs):
        '''
        Run the layers
        This will bulid the graph
        This function will connect the prev layer's output as input
        Then provide current layer's output as return value
        '''
        raise NotImplementedError

class GraphConvLayer(BaseLayer):
    '''
    Two layer GCN
    Semi-Supervised Classfication with Graph Convolution Networks, Kipf
    Model:
        Z = f(X, A) = softmax(A RELU(AXW(0))W(1))
    A = D^-0.5 L D^-0.5 (Renomalized Laplacian)
    X is the feature matrix
    NOTE: There is no bias or dropout in the orgin model
    
    '''
    def __init__(self,
                 adjancy,
                 input_dim, output_dim,
                 activation_func,
                 name,
                 dropout_prob = None,
                 bias = False,
                 sparse = False,):
        super(GraphConvLayer, self).__init__(
                                            input_dim, output_dim,
                                            activation_func,
                                            name,
                                            dropout_prob,
                                            bias,
                                            sparse
                                            )

        self.adjancy = adjancy

        
        #Define layers' variable
        with tf.variable_scope(self.name + '_var'):
            self.weights = glort_init([input_dim, output_dim], name = 'weights')
            self.weight_decay_vars.append(self.weights)
        
        #If bias is used
            if self.bias:
                self.bias = tf.zeros([output_dim], name = 'bias')
                self.weight_decay_vars.append(self.bias)    
    def run(self, inputs, num_features_nonzero = None):
        '''
        Inputs are features, Since the feateure map will change through the network
        The symmertic normalized Laplacian matrix at the first layer
        Then the convoluted matrix in the following layers
        '''
        if not self.dropout_prob:
            pass

        else:
            if self.sparse:
                inputs = sparse_dropout(inputs, 1 - self.dropout_prob, num_features_nonzero)
            else:
                inputs = tf.nn.dropout(inputs, 1 - self.dropout_prob)
        
        #Do convolution
        output = graph_conv(inputs, self.adjancy, self.weights, self.sparse)

        #bias
        if self.bias != None:
            output += self.bias

        #activation
        return self.activation_func(output)


class DenseLayer(BaseLayer):
    '''
    Dense Layer
    '''
    def __init__(self,
                 adjancy,
                 input_dim, output_dim,
                 activation_func,
                 name,
                 dropout_prob = None,
                 bias = False,
                 sparse = False):
        super(DenseLayer, self).__init__(
                                            input_dim, output_dim,
                                            activation_func,
                                            name,
                                            dropout_prob,
                                            bias,
                                            sparse
                                            )

        self.adjancy = adjancy

        #Define layer's variables
        with tf.variable_scope(self.name + '_var'): 
            self.weights = glort_init([input_dim, output_dim], name = 'weights')


            #if bias is used
            if self.bias:
                self.bias = tf.zeros([output_dim], name = 'bias')


    def run(self, inputs, num_features_nonzero):
        '''
        Inputs are features or the output passed by the previous layer
        This will connect each layers into one compution graph
        '''


        #Note, sparse drop is not implemented
        #Since we assume that no dropout is implemented and the output of a layer is dense matrix
        #Drop out to input can be implemented befor it is feeded to the train function 
        if not self.dropout_prob:
            pass

        else:
            if self.sparse:
                inputs = sparse_dropout(inputs, 1 - self.dropout_prob, num_features_nonzero)
            else:
                inputs = tf.nn.dropout(inputs, 1 - self.dropout_prob)


        #Do the calculation
        if self.sparse:
            output = tf.sparse_tensor_dense_matmul(inputs, self.weights)
        else:
            output = tf.matmul(inputs, self.weights)


        #bias
        if self.bias != None:
            output += self.bias

        #acitvation
        return self.activation_func(output)



class FirstChebLayer(BaseLayer):
    '''
    First Cheb Layer
    Note that the adjancy matrix is not normalized
    '''
    def __init__(self,
                 adjancy,
                 input_dim, output_dim,
                 activation_func,
                 name,
                 dropout_prob = None,
                 bias = False,
                 sparse = False):
        super(FirstChebLayer, self).__init__(
                                            input_dim, output_dim,
                                            activation_func,
                                            name,
                                            dropout_prob,
                                            bias,
                                            sparse
                                            )

        self.adjancy = adjancy

        #Define layer's variables
        with tf.variable_scope(self.name + '_var'): 
            self.weights_0 = glort_init([input_dim, output_dim], name = 'weights_0')
            self.weights_1 = glort_init([input_dim, output_dim], name = 'weights_1')


            #if bias is used
            if self.bias:
                self.bias = tf.zeros([output_dim], name = 'bias')


    def run(self, inputs, num_features_nonzero):
        '''
        Inputs are features or the output passed by the previous layer
        This will connect each layers into one compution graph
        '''


        #Note, sparse drop is not implemented
        #Since we assume that no dropout is implemented and the output of a layer is dense matrix
        #Drop out to input can be implemented befor it is feeded to the train function 
        if not self.dropout_prob:
            pass

        else:
            if self.sparse:
                inputs = sparse_dropout(inputs, 1 - self.dropout_prob, num_features_nonzero)
            else:
                inputs = tf.nn.dropout(inputs, 1 - self.dropout_prob)



        if self.sparse:
            XW_0 = tf.sparse_tensor_dense_matmul(inputs, self.weights_0)
            XW_1 = tf.sparse_tensor_dense_matmul(inputs, self.weights_1)
            second_part = tf.sparse_tensor_dense_matmul(self.adjancy, XW_1)
            output = tf.add(XW_0, second_part)
        else:
            XW_0 = tf.matmul(inputs, self.weights_0)
            XW_1 = tf.matmul(inputs, self.weights_1)
            second_part = tf.sparse_tensor_dense_matmul(self.adjancy, XW_1)
            output = tf.add(XW_0, second_part)


        #bias
        if self.bias != None:
            output += self.bias

        #acitvation
        return self.activation_func(output)

class GraphAttentionLayer(BaseLayer):
    '''
    Graph Attention Layer
    attention head is the number of attention heads, default = 1
    aggregate have two values: concate, ave
    concate will concate all the ouputs, used in hidded layers
    and ave will average the outputs, used in the output layer
    '''
    def __init__(self,
                 adjancy,
                 input_dim, output_dim,
                 activation_func,
                 name,
                 total_nodes,
                 attention_head = 1,
                 dropout_prob = None,
                 bias = False,
                 sparse = False,
                 aggregate_mode = 'concate'):
        super(GraphAttentionLayer, self).__init__(
                                            input_dim, output_dim,
                                            activation_func,
                                            name,
                                            dropout_prob,
                                            bias,
                                            sparse
                                            )

        self.adjancy = adjancy
        self.attention_head = attention_head
        self.aggregate_mode = aggregate_mode
        self.total_nodes = total_nodes

        #Define layer's variables
        #The number of weights and attention is equal to the number of attention heads
        self.weights = []
        self.attention = []
        self.pre_weights = []
        with tf.variable_scope(self.name + '_var'): 
            #Add weights and attention
            for i in range(self.attention_head):
                self.weights.append(glort_init([output_dim, input_dim], name = 'weights_' + str(i)))
                self.pre_weights.append(glort_init([output_dim, input_dim], name = 'pre_weights_' + str(i)))
                self.attention.append(tf.zeros([output_dim*2], name = 'attention_' + str(i)))

            
            #if bias is used
            if self.bias:
                if aggregate_mode == 'concate':
                    self.bias = tf.zeros([output_dim*attention_head], name = 'bias')
                elif aggregate_mode == 'ave':
                    self.bias = tf.zeros([output_dim], name = 'bias')
                else:
                    raise "Invalid value for aggregate_mode"
            

    def run(self, inputs, num_features_nonzero):
        '''
        Inputs are features or the output passed by the previous layer
        This will connect each layers into one compution graph
        '''


        #Note, sparse drop is not implemented
        #Since we assume that no dropout is implemented and the output of a layer is dense matrix
        #Drop out to input can be implemented befor it is feeded to the train function 
        if not self.dropout_prob:
            pass

        else:
            if self.sparse:
                inputs = sparse_dropout(inputs, 1 - self.dropout_prob, num_features_nonzero)
            else:
                inputs = tf.nn.dropout(inputs, 1 - self.dropout_prob)


        #Do the calculation
        WX_T = []
        if self.sparse:
            #Compute a list of WX_T, X is a sparse tensor
            #So, compute (WX_T)_T = XW_T
            #Then transpose it back
            for i in range(self.attention_head):
                mid_value = tf.sparse_tensor_dense_matmul(inputs, tf.transpose(self.weights[i]))
                WX_T.append(tf.transpose(mid_value))

        else:
            #Directly compute WX_T
            for i in range(self.attention_head):
                WX_T.append(tf.matmul(self.weights[i], tf.transpose(inputs)))

        #Compute a_T[Wh_i||Wh_j]
        #Note the concatention is calculted later
        #AWX_T_1 is the front part of the multiplication
        #AWX_T_2 is the back part of the multiplicationh
        #each of them is a #NODE vector

        AWX_T_1 = []
        AWX_T_2 = []

        for i in range(self.attention_head):
            AWX_T_1.append(tf.einsum('i,kj->j', self.attention[i][:self.output_dim], WX_T[i]))
            AWX_T_2.append(tf.einsum('i,kj->j', self.attention[i][self.output_dim+1: ], WX_T[i]))

        #Compute attention coeffcients
        attention_coffe = []

        for i in range(self.attention_head):
            diag = tf.matrix_diag(AWX_T_1[i])
            row_stack = tf.stack([AWX_T_2[i]] * self.total_nodes)
            attention_coffe.append(tf.matmul(diag, row_stack))

        #Mask the coeffcient matrix by adjancy matrix
        #And use LeakyRelu, 0.2
        #compute softmax over row
        for i in range(self.attention_head):     
            attention_coffe[i] = mask_by_adj(attention_coffe[i], self.adjancy)
            attention_coffe[i] = tf.nn.leaky_relu(attention_coffe[i], alpha = 0.2)
            attention_coffe[i] = tf.nn.softmax(attention_coffe[i])

        #Compute the predct
        #For each attention coffecients matrix A and weight matrix W
        #output = WX_TA_T
        output = []
        mid_value = None
        for i in range(self.attention_head):
            if self.sparse:
                mid_value = tf.sparse_tensor_dense_matmul(inputs, tf.transpose(self.pre_weights[i]))
                mid_value = tf.transpose(mid_value)
            else:
                mid_value = tf.matmul(self.pre_weights[i], tf.transpose(inputs))
                
            output.append(tf.matmul(mid_value, tf.transpose(attention_coffe[i])))
            

        if self.aggregate_mode == 'concate':
            #Concate the matrix
            output = tf.concat(output, axis = 0)

        elif self.aggregate_mode == 'ave':
            #Ave over output_matrix
            len_output = len(output)
            output = tf.add_n(output)
            output = output/len_output
        else:
            raise "aggregate_mode has a invalid value"

        #Transpose the output
        output = tf.transpose(output)

        #bias
        if self.bias != None:
            output += self.bias

        #acitvation
        return self.activation_func(output)







        


