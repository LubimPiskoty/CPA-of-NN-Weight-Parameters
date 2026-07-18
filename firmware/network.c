#include "network.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void free_network(network *net) {
  // free the dynamically allocated fields inside the network struct
  for (int i = 0; i < net->num_layers; i++) {
    for (int j = 0; j < net->layers[i].num_neurons; j++) {
      if (net->layers[i].neurons[j].weights != NULL)
        free(net->layers[i].neurons[j].weights);
    }
    free(net->layers[i].neurons);
  }
  free(net->layers);
}

/*
 * Prints out the values contained withing the network - number of layers, and
 * then for each layer prints out each neuron for each neuron this prints out
 * the a value, the z value, and the weight values (an array of size equal to
 * the number of neurons in the previous layer - except for the first layer -
 * the input layer )
 */
void print_network(network net) {
  printf("\n");
  printf("---------------------------------------------------------------------"
         "---------------------------------------------------------------------"
         "-----------------------\n");
  printf("Network - num_layers = %d\n", net.num_layers);
  for (int i = 0; i < net.num_layers; i++) {
    printf("Layer %d:\n", i);
    for (int j = 0; j < net.layers[i].num_neurons; j++) {
      printf("\tNeuron %d | a=%f z=%f\t| ", j, net.layers[i].neurons[j].a,
             net.layers[i].neurons[j].z);
      if (i >= 1) {
        printf("\tWeights: {");
        for (int k = 0; k < net.layers[i - 1].num_neurons; k++) {
          printf("%f", net.layers[i].neurons[j].weights[k]);
          if (k < net.layers[i - 1].num_neurons - 1)
            printf(", ");
          else
            printf("}");
        }
      }
      printf("\n");
    }
  }
  printf("---------------------------------------------------------------------"
         "---------------------------------------------------------------------"
         "-----------------------\n");
}

neuron create_neuron(void *weights, int num_in_weights, int layer_idx,
                     int neuron_idx) {
  neuron new_neuron;
  new_neuron.a = 0.5;
  new_neuron.z = 0.0;
  new_neuron.bias = 0.0;
  new_neuron.num_weights = num_in_weights;
  new_neuron.weights = num_in_weights > 0
                           ? (float *)malloc(num_in_weights * sizeof(float))
                           : NULL;

  if (weights != NULL) {
    for (int i = 0; i < num_in_weights; i++) {
      new_neuron.weights[i] = ((float **)weights)[neuron_idx][i];
    }
  }
  return new_neuron;
}

layer create_layer(int num_neurons) {
  layer lay;
  lay.num_neurons = num_neurons;
  lay.neurons = (neuron *)malloc(num_neurons * sizeof(neuron));
  return lay;
}

network create_network(int num_layers) {
  network net;
  net.num_layers = num_layers;
  net.layers = (layer *)malloc(num_layers * sizeof(layer));
  return net;
}

network init_network(int num_layers, int *num_neurons, void *weights) {
  network net = create_network(num_layers);
  int curr_layer_idx, curr_neuron_idx;
  for (curr_layer_idx = 0; curr_layer_idx < num_layers; curr_layer_idx++) {
    net.layers[curr_layer_idx] = create_layer(num_neurons[curr_layer_idx]);
  }
  // create neurons for the first (input) layer - they dont have weights
  for (curr_neuron_idx = 0; curr_neuron_idx < net.layers[0].num_neurons;
       curr_neuron_idx++) {
    net.layers[0].neurons[curr_neuron_idx] =
        create_neuron(NULL, 0, 0, curr_neuron_idx);
  }
  // For each following layer create neurons with number of weights eqaual to
  // the number of neurons in the previous layer
  for (curr_layer_idx = 1; curr_layer_idx < num_layers; curr_layer_idx++) {
    int prev_layer_idx = curr_layer_idx - 1;
    for (curr_neuron_idx = 0;
         curr_neuron_idx < net.layers[curr_layer_idx].num_neurons;
         curr_neuron_idx++) {
      net.layers[curr_layer_idx].neurons[curr_neuron_idx] =
          create_neuron(weights, net.layers[prev_layer_idx].num_neurons,
                        curr_layer_idx, curr_neuron_idx);
    }
  }
  return net;
}

network forward(network net) {
  volatile int curr_layer_idx, curr_neuron_idx, prev_layer_neuron_idx;
  // for each layer
  for (curr_layer_idx = 1; curr_layer_idx < net.num_layers; curr_layer_idx++) {

    int prev_layer_idx = curr_layer_idx - 1;
    // for each neuron in this layer
    for (curr_neuron_idx = 0;
         curr_neuron_idx < net.layers[curr_layer_idx].num_neurons;
         curr_neuron_idx++) {
      net.layers[curr_layer_idx].neurons[curr_neuron_idx].z =
          net.layers[curr_layer_idx].neurons[curr_neuron_idx].bias;

      // for all neurons on the previous layer
      for (prev_layer_neuron_idx = 0;
           prev_layer_neuron_idx < net.layers[prev_layer_idx].num_neurons;
           prev_layer_neuron_idx++) {
        net.layers[curr_layer_idx].neurons[curr_neuron_idx].z =
            net.layers[curr_layer_idx].neurons[curr_neuron_idx].z +
            ((net.layers[curr_layer_idx]
                  .neurons[curr_neuron_idx]
                  .weights[prev_layer_neuron_idx]) *
             (net.layers[prev_layer_idx].neurons[prev_layer_neuron_idx].a));
        // We are looking for THIS MULTIPLICATION
      }
      // get a values
      net.layers[curr_layer_idx].neurons[curr_neuron_idx].a =
          net.layers[curr_layer_idx].neurons[curr_neuron_idx].z;
      // apply relu
      if (curr_layer_idx < net.num_layers - 1) {
        if ((net.layers[curr_layer_idx].neurons[curr_neuron_idx].z) < 0) {
          net.layers[curr_layer_idx].neurons[curr_neuron_idx].a = 0;
        } else {
          net.layers[curr_layer_idx].neurons[curr_neuron_idx].a =
              net.layers[curr_layer_idx].neurons[curr_neuron_idx].z;
        }
      }
      // apply sigmoid to the last layer
      else {
        net.layers[curr_layer_idx].neurons[curr_neuron_idx].a =
            1 /
            (1 + exp(-net.layers[curr_layer_idx].neurons[curr_neuron_idx].z));
      }
    }
  }
  return net;
}
