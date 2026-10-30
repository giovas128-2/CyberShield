import argparse
import socket
import time


DESTINATION = "172.25.176.1"
PORT = 8765

PAYLOAD = (
    b"CYBERSHIELD-EXFIL-DEMO-"
    * 4096
)


def send_demo(megabytes):
    total_bytes = (
        megabytes * 1_000_000
    )

    sent = 0

    print(
        "[EXFIL-DEMO] Transferencia sintética iniciada"
    )

    print(
        f"[EXFIL-DEMO] Destino: {DESTINATION}:{PORT}"
    )

    print(
        f"[EXFIL-DEMO] Objetivo: {megabytes} MB"
    )

    try:
        with socket.create_connection(
            (DESTINATION, PORT),
            timeout=5,
        ) as sock:

            while sent < total_bytes:
                remaining = (
                    total_bytes - sent
                )

                chunk = PAYLOAD[
                    :min(
                        len(PAYLOAD),
                        remaining,
                    )
                ]

                sock.sendall(
                    chunk
                )

                sent += len(
                    chunk
                )

                if (
                    sent % 5_000_000
                    < len(chunk)
                ):
                    print(
                        "[EXFIL-DEMO]",
                        round(
                            sent / 1_000_000,
                            1,
                        ),
                        "MB enviados",
                        flush=True,
                    )

                time.sleep(
                    0.01
                )

    except (
        ConnectionRefusedError,
        ConnectionResetError,
        TimeoutError,
        OSError,
    ) as exc:
        print(
            "[EXFIL-DEMO] Transferencia bloqueada/interrumpida:",
            exc,
        )

        print(
            "[EXFIL-DEMO] Bytes enviados antes del bloqueo:",
            sent,
        )

        return

    print(
        "[EXFIL-DEMO] Transferencia terminada:",
        sent,
        "bytes",
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Transferencia sintética controlada "
            "para CyberShield."
        )
    )

    parser.add_argument(
        "--mb",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    if not 10 <= args.mb <= 100:
        raise SystemExit(
            "Usa entre 10 y 100 MB."
        )

    send_demo(
        args.mb
    )


if __name__ == "__main__":
    main()
