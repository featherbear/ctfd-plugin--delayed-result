# Delayed Result Challenge plugin for CTFd

This plugin adds a `delayed` challenge type, where the results of a challenge is **held** until a given `expiry` time.

Whilst the expiry time has not elapsed, the submission is marked as "incorrect".

When the expiry time has elapsed, future submissions function as normal.
For any previous submissions, the latest **held** submission is checked

It is also triggered...

* On CTFd start
* On HTTP_GET(`/plugin/do_update_delayed_result`)
* (TODO) Every minute

## Installation

Clone this repository into `plugins/delayed_result`.  
Or if your CTFd configuration is set up with IaC, then use a Git submodule.

## Local testing

```sh
docker compose up -d
```

This starts CTFd on <http://localhost:8000> with the plugin mounted from this
directory. On the first run it skips the setup wizard and creates:

* `student` / `password` and `admin` / `password`
* a `Delayed challenge` (flag `flag{delayed}`) whose results are released
  `SEED_DELAY_MINUTES` (default 3) after seeding

Log in as `student` and submit to see the wait message and countdown. Held
submissions are only turned into solves when CTFd starts or
`/plugin/do_update_delayed_result` is requested, so after the release time run
`docker compose restart ctfd` (or request that endpoint) to see the solve.

Template and JavaScript changes apply when the challenge is reopened; Python
changes need `docker compose restart ctfd`. To start again with a fresh
challenge, run `docker compose down -v` and then `docker compose up -d`.
