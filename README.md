# jobq

One door for heavy jobs across a handful of machines. Every job runs in its own systemd user unit inside a cgroup slice, so a test run or a build cannot starve the rest of the box.

Why: with several people or agents sharing a few machines, unbounded `pytest` or build runs pile up and hang each other. `jobq` puts each class of job behind a
number of concurrent slots (flock), a slice with CPU/IO weight, memory and runtime caps, and a thermal hold. It can also pick the machine with room and rsync a checkout there first.

## Install

Python 3.9+ (3.11+ to read the TOML config), a systemd user session, and for several machines `ssh` keys and `rsync`. Copy `bin/jobq` onto the `PATH` of every machine.
Copy `systemd/*.slice` to `~/.config/systemd/user/` and run `systemctl --user daemon-reload` to give the slices their weights.

## Configure

`cp config.example.toml ~/.config/jobq/config.toml` (or set `JOBQ_CONFIG`). Define `[nodes.NAME]` (ssh alias, extra systemd properties, optional quiet markers),
`default_node`, `sync_roots`, and per-class `slice`, `slots`, `memory_max`, `runtime_max`, `env`, `auto`, `serialize`. Without any node, jobs simply run locally.
A thermal monitor may write `~/.cache/jobq/no-new-jobs` (hold) or `jobq.cap` (slot cap) to throttle new work.

## Example

```
jobq run unit-tests --class test -- python3 -m pytest -q       # placed on the node with room, streamed back, exit code preserved
jobq run release-gate --class gate --node big -- ./gate.sh     # gates serialize on one node
jobq ls --node big; jobq tail unit-tests -f
```

## Tests

`python3 -m unittest discover -s tests` checks config merging, probe parsing, node qualification, the unit command and slot locking.

## License

Apache-2.0, see `LICENSE` and `NOTICE`.
