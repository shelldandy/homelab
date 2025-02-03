#!/bin/bash

# Handle RAR files
if ls "$1"/*.rar 1>/dev/null 2>&1; then
  unrar x "$1"/*.rar "$1"
fi

# Handle ZIP files
if ls "$1"/*.zip 1>/dev/null 2>&1; then
  unzip "$1"/*.zip -d "$1"
fi
