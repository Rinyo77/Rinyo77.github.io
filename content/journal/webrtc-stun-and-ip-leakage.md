+++
title = 'WebRTC, STUN, and IP Leakage'
date = 2026-09-16T00:00:00Z
description = 'Notes on WebRTC, STUN communication, and IP exposure through a proxy chain.'
topics = ['Security Notes']
tags = ['WebRTC', 'STUN', 'networking']
draft = false
+++

## Q

Is it WebRTC that leaks the source IP, or does STUN communication obtain the source IP?

## A

In a browser context, STUN communication cannot be initiated directly, but the JavaScript WebRTC API can indirectly trigger STUN communication and obtain the public source IP from the response. Before 2022, the JavaScript WebRTC API could also directly obtain the internal IP address; this process was unrelated to STUN communication.

## Q

If machine A uses a browser with a proxy chain, passing serially through B0, B1, ..., BN to access a page on machine C, can C obtain the exit IPs of B0, B1, ..., BN?

## A

JavaScript embedded in C's page executes in A's browser. A communicates directly with the STUN server S, and this communication does not pass through B0, B1, ..., BN. S returns A's exit IP to A, and A submits its own exit IP to C. C therefore sees both A's exit IP and BN's exit IP, but cannot see the exit IPs of B0 or B1; the intermediate nodes remain hidden.
