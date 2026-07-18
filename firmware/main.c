#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "network.h"
#include "network_config.h"

#include "hal.h"
#include "simpleserial.h"

/// This function will handle the 'p' command send from the capture board.
uint8_t handle(uint8_t *buf, uint8_t len) {
  int num_layers = NET_NUM_LAYERS;
  int *num_neurons_arr = NET_NUM_NEURONS;

  // Initialize the network with the pre-defined structure
  network net =
      init_network(num_layers, num_neurons_arr, net_config_layer_weights);

  // Change the input of the first neuron in the first layer to the provided
  // number convert to float from a 4-byte buffer
  float input_value;
  uint8_t input_buffer[4] = {buf[0], buf[1], buf[2], buf[3]};
  memcpy(&input_value, input_buffer, sizeof(float));
  net.layers[0].neurons[0].a = input_value;

  // Start Measurement
  trigger_high();
  net = forward(net);
  // Stop Measurement
  trigger_low();

  // free dynamically allocated memory
  free_network(&net);

  simpleserial_put('r', len, buf);

  return 0;
}

int main(void) {
  srand(time(NULL));
  // Initialize network weights
  init_weights();
  // Setup the specific chipset.
  platform_init();
  // Setup serial communication line.
  init_uart();
  // Setup measurement trigger.
  trigger_setup();

  simpleserial_init();

  // Insert your handlers here.
  simpleserial_addcmd('p', 16, handle);
}
