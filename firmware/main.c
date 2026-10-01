#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "network.h"
#include "network_config.h"

#include "hal.h"
#include "simpleserial.h"

// Set at build time only (make IS_ATTACK_MODE=1); the payload cannot change it.
// volatile keeps the compiler from dropping the unused branch, which would
// change the code layout between the profiling and attack builds.
#ifdef IS_ATTACK_MODE
static volatile const uint8_t is_profiling = 0;
#else
static volatile const uint8_t is_profiling = 1;
#endif /* ifdef IS_ATTACK_MODE */

// Range of the random weights used while profiling (same as WEIGHT_LOW/HIGH in
// capture/configs/cw_config.py)
#define RANDOM_WEIGHT_MAX 2.0f

/// Uniform random float in [-RANDOM_WEIGHT_MAX, RANDOM_WEIGHT_MAX].
static float random_weight(void) {
  return ((float)rand() / (float)RAND_MAX) * (2.0f * RANDOM_WEIGHT_MAX) -
         RANDOM_WEIGHT_MAX;
}

/// Handles the 'k' command: seeds the RNG with the 4-byte payload (uint32) and
/// sets the weights used by every following 'p' command, so the host changes
/// weights once per batch of traces instead of once per trace.
/// Profiling: every weight is random from the seed. Attack: the same work is
/// done but the fixed weights from network_config.h are kept.
/// Replies with the attacked (first) weight so the host knows its value.
uint8_t set_weights(uint8_t *buf, uint8_t len) {
  uint32_t seed;
  memcpy(&seed, buf, sizeof(uint32_t));
  srand(seed);

  for (int n = 0; n < 5; n++)
    for (int w = 0; w < 7; w++) {
      float r = random_weight();
      net_config_weights.lay1_weights[n][w] =
          is_profiling ? r : net_config_weights.lay1_weights[n][w];
    }
  for (int n = 0; n < 4; n++)
    for (int w = 0; w < 5; w++) {
      float r = random_weight();
      net_config_weights.lay2_weights[n][w] =
          is_profiling ? r : net_config_weights.lay2_weights[n][w];
    }
  for (int n = 0; n < 3; n++)
    for (int w = 0; w < 4; w++) {
      float r = random_weight();
      net_config_weights.lay3_weights[n][w] =
          is_profiling ? r : net_config_weights.lay3_weights[n][w];
    }

  uint8_t out[4];
  memcpy(out, &net_config_weights.lay1_weights[0][0], sizeof(float));
  simpleserial_put('r', sizeof(out), out);

  return 0;
}

/// This function will handle the 'p' command send from the capture board.
/// Only the input changes here; the weights are the ones set by 'k'.
uint8_t handle(uint8_t *buf, uint8_t len) {
  int num_layers = NET_NUM_LAYERS;
  int *num_neurons_arr = NET_NUM_NEURONS;

  // Initialize the network with the current weights
  network net =
      init_network(num_layers, num_neurons_arr, net_config_layer_weights);

  // Change the input of the first neuron in the first layer to the provided
  // number convert to float from a 4-byte buffer
  float input_value;
  memcpy(&input_value, buf, sizeof(float));

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
  // Initialize network weights to the fixed ones. Profiling replaces them
  // with random ones through the 'k' command; the attack build keeps them.
  init_weights();
  // Setup the specific chipset.
  platform_init();
  // Setup serial communication line.
  init_uart();
  // Setup measurement trigger.
  trigger_setup();

  simpleserial_init();

  // Insert your handlers here.
  simpleserial_addcmd('k', 4, set_weights);
  simpleserial_addcmd('p', 16, handle);

  while (1)
    simpleserial_get();
}
