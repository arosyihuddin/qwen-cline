import random


def tebak_angka():
    print("Selamat datang di permainan Tebak Angka!")
    print(
        "Komputer akan memilih sebuah angka antara 1 hingga 100. Coba tebak angka tersebut!"
    )

    angka_rahasia = random.randint(1, 100)
    tebakan = None
    jumlah_tebakan = 0

    while tebakan != angka_rahasia:
        try:
            tebakan = int(input("Masukkan tebakan Anda: "))
            jumlah_tebakan += 1

            if tebakan < angka_rahasia:
                print("Terlalu rendah! Coba lagi.")
            elif tebakan > angka_rahasia:
                print("Terlalu tinggi! Coba lagi.")
            else:
                print(
                    f"Selamat! Anda berhasil menebak angka {angka_rahasia} dalam {jumlah_tebakan} kali tebakan."
                )
        except ValueError:
            print("Harap masukkan angka yang valid.")


if __name__ == "__main__":
    tebak_angka()
