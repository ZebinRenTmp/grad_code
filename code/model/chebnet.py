import tensorflow as tf
from .base_model import BaseModel
from .layers import *
from .model_utils import *

class ChebNet(BaseModel):
    def __init__(self,
         hidden_num, hidden_dim,
         input_dim, output_dim,
         node_num, cate_num,
         learning_rate, epochs,
         weight_decay, early_stopping,
         activation_func, 
         dropout_prob,
         bias, optimizer,
         name,
         poly_order):
        super(ChebNet, self).__init__(
            hidden_num, hidden_dim,
            input_dim, output_dim,
            learning_rate, epochs,
            weight_decay, early_stopping,
            name)
        
        #End
        self.total_nodes = node_num
        self.total_cates = output_dim
        self.activation_func = activation_func
        self.dropout_prob = dropout_prob
        self.bias = bias
        self.poly_order = poly_order

  
        #Add placeholders
        #Note, this dictionary is used to create feed dicts
        #, shape=(self.total_nodes, self.input_dim)
        self.placeholders = {}
        self.placeholders['features'] = tf.sparse_placeholder(tf.float32, name='Feature')
        self.placeholders['adj'] = [tf.sparse_placeholder(tf.float32, shape=(self.total_nodes, self.total_nodes), name='Adjancy' + str(i)) for i in range(self.poly_order)]
        self.placeholders['labels'] = tf.placeholder(tf.int32, shape=(self.total_nodes, self.total_cates), name='labels')
        self.placeholders['mask'] = tf.placeholder(tf.int32, shape=(self.total_nodes), name='mask')
        self.placeholders['num_features_nonzero'] = tf.placeholder(tf.int32, name='num_features_nonzero')

        self.adjancy = self.placeholders['adj']
        self.inputs = self.placeholders['features']
        self.label = self.placeholders['labels']
        self.mask = self.placeholders['mask']
        self.num_features_nonzero = self.placeholders['num_features_nonzero']

        self.optimizer = optimizer(learning_rate=self.learning_rate)

        self.build()


    def _add_layers(self):
        self.layers.append(
            ChebLayer(self.adjancy,
                self.hidden_dim[0], self.hidden_dim[1],
                self.activation_func,
                self.name + '_0',
                self.dropout_prob,
                self.bias,
                True,
                self.poly_order
                ))
        self.layers.append(
            ChebLayer(self.adjancy,
                self.hidden_dim[1], self.hidden_dim[2],
                self.activation_func,
                self.name + '_1',
                self.dropout_prob,
                self.bias,
                False,
                self.poly_order
                ))
  
    def _loss(self):
        '''
        Define loss function
        '''
        #loss
        loss = masked_softmax_cross_entropy(self.outputs, self.label, self.mask)
        
        #Regularization, weight_decay
        for each_layer in self.layers: #[0: -1]:
            for var in each_layer.weight_decay_vars:
                loss += self.weight_decay * tf.nn.l2_loss(var)


        return loss
    
    def _accuracy(self):
        '''
        Define accuracy
        '''

        accuracy = masked_accuracy(self.outputs, self.label, self.mask)

        return accuracy
        

    def train(self, sess, adj, features, train_label, val_label, train_mask, val_mask, num_features_nonzero):
        '''
        Train the model
        '''
        #Loss: Saves a list of the loss
        loss_list = []
        cost_list = []
        acc_list = []
        #Construct the feed dict
        print(self.num_features_nonzero)

        feed_dict = {
          #self.adjancy: adj,
          self.inputs: features,
          self.label: train_label,
          self.mask: train_mask,
          self.num_features_nonzero: num_features_nonzero
        }
        feed_dict.update({self.adjancy[i]: adj[i] for i in range(self.poly_order)})

        feed_dict_val = {
          #self.adjancy: adj,
          self.inputs: features,
          self.label: val_label,
          self.mask: val_mask,
          self.num_features_nonzero: num_features_nonzero       
        }
        feed_dict_val.update({self.adjancy[i]: adj[i] for i in range(self.poly_order)})

        sess.run(tf.global_variables_initializer())

        #Train precedure
        for epoch in range(self.epochs):

            loss, train_accu,  _ = sess.run([self.loss, self.accuracy, self.opt_op],  feed_dict=feed_dict)
            loss_list.append(loss)

            cost, val_accu = sess.run([self.loss, self.accuracy], feed_dict=feed_dict_val)
            cost_list.append(cost)
            acc_list.append(val_accu)

            print('epochs: ', epoch, 'loss: ', loss, 'train_accu: ', train_accu, 'cost: ', cost, train_accu, 'accuracy: ',  val_accu)
            
            #Test early stopping
            if early_stopping(cost_list, epoch, self.early_stopping):
                print("Early stopping")
                break


    

    def predict(self, sess, adj, features, label, mask, num_features_nonzero):
        '''
        Predict, a cate-index representation will be provided
        '''
        feed_dict = {
            #self.adjancy: adj,
            self.inputs: features,
            self.label: label,
            self.mask: mask,
            self.num_features_nonzero: num_features_nonzero
        }
        feed_dict.update({self.adjancy[i]: adj[i] for i in range(self.poly_order)})

        outputs = sess.run(self.outputs, feed_dict=feed_dict)

        cate_index = tf.argmax(outputs, 1)

        return cate_index

    def test(self, sess, adj, features, label, mask, num_features_nonzero):
        '''
        Test the model, return accuracy
        '''
        feed_dict = {
            #self.adjancy: adj, 
            self.inputs: features,
            self.label: label,
            self.mask: mask,
            self.num_features_nonzero: num_features_nonzero
        }
        feed_dict.update({self.adjancy[i]: adj[i] for i in range(self.poly_order)})

        accu = sess.run(self.accuracy, feed_dict=feed_dict)

        return accu