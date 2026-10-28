/*
 * Phyphox BLE bridge for the BWOFSS orthodontic force reader.
 *
 * The reader (bwofss_reader.py) sends one force value per line over USB
 * serial at 115200 baud. This sketch reads that line and forwards the value
 * to the phyphox app over Bluetooth Low Energy, where it is plotted as
 * "Orthodontic Force Monitor".
 *
 * Hardware: a BLE-capable Arduino board supported by the phyphoxBle library
 * (for example Arduino Nano 33 BLE / Nano 33 IoT).
 *
 * Install the "phyphoxBle" library through the Arduino Library Manager.
 *
 * Copyright (c) 2024 Pengyu Li
 * SPDX-License-Identifier: MIT
 */

#include <phyphoxBle.h>

const unsigned long SERIAL_BAUD = 115200;

void setup()
{
  Serial.begin(SERIAL_BAUD);

  PhyphoxBLE::start("Orthodontic Force");

  PhyphoxBleExperiment experiment;
  experiment.setTitle("Orthodontic Force Monitor");
  experiment.setCategory("Orthodontic Force");
  experiment.setDescription("Battery-free wireless orthodontic force sensor");

  PhyphoxBleExperiment::View view;
  view.setLabel("Force");

  PhyphoxBleExperiment::Graph graph;
  graph.setLabel("Orthodontic force");
  graph.setUnitX("s");
  graph.setUnitY("N");
  graph.setLabelX("time");
  graph.setLabelY("Force");
  graph.setXPrecision(3);
  graph.setYPrecision(3);
  graph.setChannel(0, 1);

  view.addElement(graph);
  experiment.addView(view);
  PhyphoxBLE::addExperiment(experiment);
}

void loop()
{
  if (Serial.available() > 0)
  {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.length() > 0)
    {
      float force = line.toFloat();
      PhyphoxBLE::write(force);
    }
  }

  // Required on some boards (e.g. Arduino Nano 33 IoT); harmless elsewhere.
  PhyphoxBLE::poll();
}
