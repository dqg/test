#!/bin/sh

[ -d pm ] ||
    while read -r x; do
        l=$(curl -s "https://f-droid.org/en/packages/$x/" | grep -om1 "https://.*$x.*\.apk")
        wget -q --show-progress -P pm "$l" || exit 1
    done < pkg.txt
echo pm/* | xargs -n1 -P0 adb install -g
adb push bg.jpg /sdcard