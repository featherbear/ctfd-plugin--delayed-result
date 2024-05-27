# Delayed Result Challenge plugin for CTFd

This plugin adds a `delayed` challenge type, where the results of a challenge is held until a given `expiry` time.

Whilst the expiry time has not elapsed, the submission is marked as "incorrect".

When the expiry time has elapsed, future submissions function as normal.
For any previous submissions, the latest incorrect submissions are checked
* On CTFd load
* On HTTP_GET(`/plugin/do_update_delayed_result`)
* (TODO) Every minute

## Installation

Clone this repository into `plugins/delayed_result`.  
Or if your CTFd configuration is IaC, then use a Git submodule.
