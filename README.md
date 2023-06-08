# DinDong

This is a Python script that allows you to play a DingDong on a Sonos speaker using a local HTTP server. The script uses the soco library to control the Sonos speaker and the click library for command line interface.


# How to use it

```
pip install dingdong-sonos
dingdong
```

You can adjust the volume or set the sonos_ip:
```
dingdong --sonos_ip <ip-of-your-sonos> --volume 80