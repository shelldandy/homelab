#!/bin/bash
if ls "$1"/*.rar 1> /dev/null 2>&1; then
    unrar x "$1"/*.rar "$1"
fi
