"""Diagnostic du flux vidéo Tello — sans cv2, sans djitellopy, juste sockets bruts.

Usage :
    python scripts/diag_tello_video.py

Le script :
1. Envoie 'command' puis 'streamon' au Tello sur UDP 8889
2. Écoute pendant 10s sur UDP 11111
3. Dit combien de packets ont été reçus

Si 0 packet  → problème réseau (firewall ou isolation client wifi)
Si >0 packet → cv2/FFmpeg foire mais le réseau marche
"""
import os
import socket
import sys
import time

from dotenv import load_dotenv

load_dotenv()

TELLO_IP = os.getenv("TELLO_IP", "192.168.10.1")
print(f"Tello IP attendue : {TELLO_IP}")
print()

# ----- 1. Canal de commande (UDP 8889) -----
cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cmd_sock.bind(("", 0))  # port local random
cmd_sock.settimeout(5)

def send(cmd: str) -> str:
    cmd_sock.sendto(cmd.encode(), (TELLO_IP, 8889))
    try:
        data, _ = cmd_sock.recvfrom(1024)
        return data.decode(errors="ignore").strip()
    except socket.timeout:
        return "<TIMEOUT>"

print(">>> command :", end=" ", flush=True); print(send("command"))
print(">>> streamon :", end=" ", flush=True); print(send("streamon"))

# ----- 2. Écoute UDP 11111 -----
try:
    video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    video_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
    video_sock.bind(("0.0.0.0", 11111))
    video_sock.settimeout(10)
except OSError as e:
    print(f"\n❌ Impossible d'ouvrir UDP 11111 : {e}")
    print("→ Probablement un autre processus l'utilise (autre serveur ?).")
    sys.exit(2)

print("\nÉcoute UDP 11111 pendant 10s...")
packets = 0
total_bytes = 0
sources = set()
start = time.time()

try:
    while time.time() - start < 10:
        data, addr = video_sock.recvfrom(4096)
        packets += 1
        total_bytes += len(data)
        sources.add(addr[0])
        if packets <= 3:
            print(f"  packet {packets} : {len(data)} bytes from {addr}")
except socket.timeout:
    pass

print()
print("=" * 60)
print(f"Résultat : {packets} packets reçus, {total_bytes/1024:.1f} KB")
if sources:
    print(f"Sources : {sources}")
print("=" * 60)

if packets == 0:
    print()
    print("❌ AUCUN PACKET REÇU")
    print()
    print("Causes possibles :")
    print("  1. Pare-feu Windows bloque UDP 11111 entrant")
    print("     → PowerShell admin :")
    print('       New-NetFirewallRule -DisplayName "Tello Video UDP 11111" '
          "-Direction Inbound -Protocol UDP -LocalPort 11111 -Action Allow")
    print()
    print("  2. Isolation client wifi (le routeur empêche les appareils")
    print("     de se voir entre eux). Désactiver dans l'admin de la box :")
    print("     'AP isolation' / 'Client isolation' / 'Wireless isolation'")
    print()
    print("  3. Le Tello s'attend à émettre vers une IP différente.")
    print("     Vérifier que votre PC est bien sur le réseau du Tello.")
else:
    print()
    print("✅ Packets reçus — le RÉSEAU marche !")
    print("   Le souci vient donc de cv2/FFmpeg côté décodage.")
    print("   On peut essayer une autre approche de capture.")

# Cleanup
cmd_sock.sendto(b"streamoff", (TELLO_IP, 8889))
cmd_sock.close()
video_sock.close()
