#!/bin/bash

set -e

gen_pw() {
    res=$(tr -dc 'A-Za-z0-9!"#$%&()*+,-/;<=>?@' </dev/urandom | head -c 20)
    echo $res
}

echo "Generating new password for user $1"
PASSWORD="$(gen_pw)"
echo "Saving credentials to plaintext file users.txt"
echo $PASSWORD | htpasswd -cip users.txt $1 >/dev/null 2>&1
echo "Hashing credential and saving to hashed-users.txt"
echo $PASSWORD | htpasswd -ciB -C 10 hashed-users.txt $1
echo "Done"
