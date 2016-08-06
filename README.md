# onestack


================ Question and Answers ====================

1. Following situation:
---------------------
2016-07-13 00:09:54,131 INFO linode: handling configuration change: installation
2016-07-13 00:09:56,952 INFO linode: linode 2091733: Apache is already installed
2016-07-13 00:09:59,085 INFO linode: linode 2091733: installing MySQL server
2016-07-13 00:10:26,766 INFO linode: linode 2091733: installing Wordpress framework
2016-07-13 00:10:52,927 INFO linode: linode 2091733: installing PHP5 language
2016-07-13 00:10:55,256 INFO main: initialization done
2016-07-13 00:10:55,258 INFO main: observing filesystem changes
2016-07-13 00:11:36,971 INFO main: ... reloading file: 2
2016-07-13 00:11:36,973 INFO linode: handling configuration change: installation
2016-07-13 00:11:39,086 INFO linode: linode 2091733: uninstalling Apache
2016-07-13 00:11:45,462 INFO linode: linode 2091733: uninstalling MySQL server
2016-07-13 00:11:49,476 INFO linode: linode 2091733: Wordpress is not installed, cannot remove
2016-07-13 00:11:51,709 INFO linode: linode 2091733: uninstalling PHP5 language
---------------------
Question: why "Wordpress is not installed, cannot remove", it's cleanly visible that Wordpress is installed above?
Answer: when Apache is being uninstalled, Wordpress is uninstalled too, because it depends on Apache.

