============================================================
nimbusdisc
============================================================

This is a a weekend hack to sync your files to a collection
of clouds.

------------------------------------------------------------
Install
------------------------------------------------------------

------------------------------------------------------------
Running
------------------------------------------------------------

------------------------------------------------------------
TODO
------------------------------------------------------------

* fs-watcher -> fs-event -> fs-event-queue
* fs-event-queue -> fs-event-processor -> pyacd-client -> nimbus
* nimbus-poller  -> nimbus-processor   -> pyacd-client -> drive
* local path -> nimbus path mapper
* exclude created files from fs-watcher
* persisted session
* persisted settings
* init.d daemon
* gtk frontend (start, stop, settings, status)
* recycle occasionally
