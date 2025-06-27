# app.py (Root Directory)
# Main entry point for the Flask application with a Tkinter UI.

import tkinter as tk
from tkinter import ttk
import webbrowser
import socket
import threading
import os
from app import create_app # Pastikan ini mengimpor fungsi create_app dari direktori app Anda

# --- Konfigurasi Aplikasi Flask ---
PORT = int(os.environ.get('PORT', 5000))
HOST = '0.0.0.0' # Mendengarkan di semua interface jaringan

def get_local_ip():
    """Mendapatkan alamat IP lokal mesin."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tidak perlu benar-benar terhubung, hanya untuk mendapatkan interface default
        s.connect(("8.8.8.8", 80)) 
        ip = s.getsockname()[0]
    except Exception as e:
        print(f"Tidak dapat mendapatkan IP lokal: {e}")
        ip = "127.0.0.1" # Fallback ke localhost
    finally:
        if s:
            s.close()
    return ip

def start_flask_app():
    """Memulai server Flask dalam thread terpisah."""
    # Buat instance aplikasi Flask
    # Konfigurasi bisa 'development', 'testing', atau 'production'
    # Anda mungkin ingin mengambil ini dari variabel lingkungan
    config_name = os.getenv('FLASK_CONFIG', 'development')
    flask_app_instance = create_app() # Menggunakan create_app dari __init__.py
    
    print(f"Memulai server Flask di http://{HOST}:{PORT}")
    try:
        # Gunakan server development Flask. Untuk produksi, pertimbangkan Gunicorn atau Waitress.
        flask_app_instance.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Gagal memulai server Flask: {e}")
        # Mungkin update UI Tkinter untuk menunjukkan error
        if root and status_label: # Pastikan root dan status_label ada
            status_label.config(text=f"Error: Server Flask gagal dimulai.\n{e}", foreground="red")


def open_browser(url):
    """Membuka URL di browser default."""
    print(f"Membuka browser ke: {url}")
    webbrowser.open_new(url)

# --- Fungsi Utama untuk UI Tkinter ---
def create_tkinter_ui():
    global root, status_label # Jadikan global agar bisa diakses oleh fungsi lain jika perlu
    root = tk.Tk()
    root.title("Server Aplikasi VidGen")
    root.geometry("450x250") # Ukuran window yang sedikit lebih besar
    root.resizable(False, False) # Mencegah perubahan ukuran window

    # Style
    style = ttk.Style()
    style.theme_use('clam') # Tema modern, bisa juga 'alt', 'default', 'classic'
    
    style.configure("TLabel", font=("Segoe UI", 10), padding=5)
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
    style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#0078D7") # Biru untuk header
    style.configure("Link.TButton", foreground="#0078D7", relief="flat")
    style.map("Link.TButton", foreground=[('active', '#00539C')])


    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.pack(expand=True, fill=tk.BOTH)

    header_label = ttk.Label(main_frame, text="Server Aplikasi VidGen Aktif", style="Header.TLabel")
    header_label.pack(pady=(0, 15))

    local_ip = get_local_ip()
    app_url_localhost = f"http://localhost:{PORT}"
    app_url_local_ip = f"http://{local_ip}:{PORT}"

    info_text = f"Server berjalan dan dapat diakses di:\n"
    info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
    info_label.pack(anchor=tk.W)

    # Tombol untuk Localhost
    open_localhost_button = ttk.Button(
        main_frame, 
        text=f"Buka di Browser (Localhost)", 
        command=lambda: open_browser(app_url_localhost),
        style="Link.TButton"
    )
    open_localhost_button.pack(pady=5, fill=tk.X)
    localhost_display_label = ttk.Label(main_frame, text=app_url_localhost, font=("Segoe UI", 9, "italic"))
    localhost_display_label.pack(anchor=tk.W, padx=5)


    # Tombol untuk IP Lokal (jika berbeda dari localhost)
    if local_ip != "127.0.0.1" and local_ip != "localhost":
        open_local_ip_button = ttk.Button(
            main_frame, 
            text=f"Buka di Browser (IP Lokal)", 
            command=lambda: open_browser(app_url_local_ip),
            style="Link.TButton"
        )
        open_local_ip_button.pack(pady=(10,5), fill=tk.X)
        local_ip_display_label = ttk.Label(main_frame, text=app_url_local_ip, font=("Segoe UI", 9, "italic"))
        local_ip_display_label.pack(anchor=tk.W, padx=5)
    
    status_label = ttk.Label(main_frame, text="Status server: Berjalan...", font=("Segoe UI", 9), foreground="green")
    status_label.pack(pady=(15,0), anchor=tk.W)

    # Pastikan aplikasi Flask berhenti saat window Tkinter ditutup
    def on_closing():
        print("Menutup aplikasi...")
        # Cara menghentikan server Flask dari thread lain bisa rumit.
        # Salah satu cara adalah dengan mengirim request shutdown ke endpoint khusus,
        # atau cara yang lebih 'keras' adalah os._exit(0) jika tidak ada cleanup penting.
        # Untuk aplikasi development, exit sederhana mungkin cukup.
        root.destroy()
        os._exit(0) # Menghentikan program secara paksa, termasuk thread Flask

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == '__main__':
    # Mulai server Flask di thread terpisah
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()

    # Buat dan jalankan UI Tkinter di thread utama
    create_tkinter_ui()
