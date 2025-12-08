# Security

The bridge is an experimental bench tool. It speaks unauthenticated UDP to a
robot on the local network, by design — see `docs/PROTOCOL.md` for why that is
a deliberate limitation and what it implies.

## What not to do

- Do not expose the robot port to the internet. There is no authentication, no
  session ID and no replay protection. Anyone who can reach the port can drive
  the motors.
- Do not run the bridge with real motors while the emergency stop path is
  untested. Test the stop first, on blocks.

## Reporting

Open an issue for anything that could move hardware unexpectedly, and include
the configuration and the log excerpt. Safety-relevant reports get priority.
