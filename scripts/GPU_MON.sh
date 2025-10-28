#!/usr/bin/env bash
watch -n 1 '
date +"%F %T";
nvidia-smi --query-gpu=name,utilization.gpu,utilization.memory,memory.total,memory.used --format=csv,noheader;
echo "--- top - 5 procs GPU mem ---";
nvidia-smi pmon -c 1 | head -n 15
'
