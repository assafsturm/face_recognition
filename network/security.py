#!/usr/bin/env python3
import socket
import json
import struct

from network.protocol import (
    generate_dh_keys,
    compute_shared_key,
    derive_aes_key,
    encrypt_message,
    decrypt_message,
    recv_all
)

def test_encryption():
    # 1) פותחים זוג סוקטים מקומיים
    sock_client, sock_server = socket.socketpair()

    # 2) סימולציה של חילוף מפתחות Diffie–Hellman
    priv_c, pub_c, p, g = generate_dh_keys()
    # שולחים צד לקוח -> שרת
    sock_client.send(json.dumps({"public": pub_c, "p": p, "g": g}).encode())

    # השרת מקבל
    dh_data = json.loads(sock_server.recv(4096).decode())
    priv_s, pub_s, _, _ = generate_dh_keys()
    # השרת שולח מפתח ציבורי חזרה
    sock_server.send(json.dumps({"public": pub_s}).encode())

    # 3) מגזרים מפתח AES משותף בשני הצדדים
    shared_c = compute_shared_key(pub_s, priv_c, p)
    shared_s = compute_shared_key(dh_data["public"], priv_s, p)
    key_c = derive_aes_key(shared_c)
    key_s = derive_aes_key(shared_s)

    # 4) שולחים הודעה לדוגמה מוצפנת מה־client ל־server
    message = {"type": "attendance", "id_number": "999999", "event": "entry"}
    # משתמשים בפונקציה מה־protocol
    encrypted = encrypt_message(key_c, message)
    sock_client.sendall(struct.pack("!I", len(encrypted)))
    sock_client.sendall(encrypted)

    # 5) השרת קורא בייט־לייט ואז מפענח
    raw_len = recv_all(sock_server, 4)
    msg_len = struct.unpack("!I", raw_len)[0]
    data = recv_all(sock_server, msg_len)

    print("🔒 Encrypted payload (hex):")
    print(data.hex(), "\n")

    decrypted = decrypt_message(key_s, data)
    print("🔓 Decrypted message (dict):")
    print(decrypted)

    # סוגרים
    sock_client.close()
    sock_server.close()

if __name__ == "__main__":
    test_encryption()
