#!/bin/bash

git pull origin master

sudo systemctl restart time-console.service

echo "Update complete"
