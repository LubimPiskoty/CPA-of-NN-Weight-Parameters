#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "network.h"
#include "network_config.h"

#include "hal.h"
#include "simpleserial.h"

// Set at build time only (make IS_ATTACK_MODE=1); the payload cannot change it.
// volatile keeps the compiler from dropping the unused branch, which would
// change the code layout between the profiling and attack builds.
#ifdef IS_ATTACK_MODE
static volatile const uint8_t use_payload_weight = 0;
#else
static volatile const uint8_t use_payload_weight = 1;
#endif /* ifdef IS_ATTACK_MODE */

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

  // Profiling: the first weight comes from the payload. Attack: it stays the
  // fixed weight from network_config.h and the payload weight is ignored.
  // Both builds run the same instructions (only the flag's value differs), so
  // the code layout and timing of the two builds are identical.
  float weight_value;
  memcpy(&weight_value, &buf[sizeof(float)], sizeof(float));

  float fixed_weight = net.layers[1].neurons[0].weights[0];
  net.layers[1].neurons[0].weights[0] =
      use_payload_weight ? weight_value : fixed_weight;

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
  // Initialize network weights. Both modes use the same fixed weights so the
  // traces match; profiling only overrides the first weight in handle().
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

  while (1)
    simpleserial_get();
}
