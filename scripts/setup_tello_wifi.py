"""Bascule un Tello EDU du mode direct (AP) vers le mode station (rejoint un wifi).

Usage :
    python scripts/setup_tello_wifi.py "<SSID>" "<password>"

Pré-requis :
- Tello EDU allumé.
- Votre PC connecté au wifi TELLO-XXXXXX (mode AP par défaut du drone).

Après exécution :
- Le Tello redémarre et rejoint le wifi spécifié.
- Reconnectez votre PC sur ce même wifi.
- Trouvez l'IP du Tello : `arp -a | findstr 60-60-1f`
- Mettez TELLO_IP=<ip> dans .env, puis lancez python server.py.

Pour revenir en mode direct (AP) : appui long 5s sur le bouton power du Tello.
"""
import sys

from djitellopy import Tello


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    ssid = sys.argv[1]
    password = sys.argv[2]

    print(">>> Connexion au Tello (vous devez être sur le wifi TELLO-XXXXXX)...")
    tello = Tello()
    tello.connect()
    battery = tello.get_battery()
    print(f"    OK. Batterie: {battery}%")

    if battery < 30:
        print("    ⚠ Batterie < 30%. Chargez avant la procédure (le drone va redémarrer).")
        sys.exit(2)

    print(f">>> Configuration : SSID='{ssid}'")
    tello.connect_to_wifi(ssid, password)

    print()
    print("=" * 60)
    print("Le Tello redémarre et tente de rejoindre votre wifi.")
    print()
    print("Étapes suivantes :")
    print(f"  1. Reconnectez votre PC au wifi '{ssid}'")
    print("  2. Trouvez l'IP du Tello :")
    print("       Windows : arp -a | findstr 60-60-1f")
    print("       (les MACs des Tello commencent par 60:60:1F)")
    print("  3. Dans .env :")
    print("       DRONE_TYPE=tello")
    print("       TELLO_IP=192.168.x.y")
    print("  4. python server.py")
    print()
    print("Pour revenir en mode direct (AP) : appui long 5s sur power du Tello.")
    print("=" * 60)


if __name__ == "__main__":
    main()
