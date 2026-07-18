
typedef struct neuron_struct {
  int num_weights;
  float *weights;
  float bias;
  float z;
  float a;
} neuron;

typedef struct layer_struct {
  int num_neurons;
  neuron *neurons;
} layer;

typedef struct network_struct {
  int num_layers;
  layer *layers;
} network;

// Utility functions
void print_network(network net);
void free_network(network *net);

// Network control
neuron create_neuron(void *weights, int num_out_weights, int layer_idx,
                     int neuron_idx);
layer create_layer(int num_neurons);
network create_network(int num_layers);
network init_network(int num_layers, int *num_neurons, void *weights);

network forward(network net);
