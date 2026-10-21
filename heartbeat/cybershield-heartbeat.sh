#!/bin/bash

curl -s -X POST http://100.77.51.7:8000/servers/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "name": "srv-yahir-01",
    "ip_address": "100.125.119.56",
    "agent": "wazuh"
  }'
