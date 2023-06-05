#!/bin/bash

stripe listen --forward-to localhost:8010/webhooks/stripe
