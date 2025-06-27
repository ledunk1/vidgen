from flask import Flask, current_app
import os

# Impor fungsi ensure_media_dirs dari routes.py
from .routes import ensure_media_dirs 
# Impor fungsi untuk memastikan file template ada saat startup
from .prompt_template_utils import load_prompt_templates # Untuk inisialisasi
# Baris berikut menyebabkan error karena puter_ai_routes.py dikosongkan/dihapus
# dan tidak lagi menjadi modul yang valid atau tidak mendefinisikan ensure_puter_media_dirs.
# from .puter_ai_routes import ensure_puter_media_dirs as ensure_puter_media_dirs_specific 


def create_app():
    """
    Factory function untuk membuat instance aplikasi Flask.
    """
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_ganti_ini_di_produksi_banget')
    if app.config['SECRET_KEY'] == 'dev_secret_key_ganti_ini_di_produksi_banget' and not app.debug:
        print("PERINGATAN: FLASK_SECRET_KEY tidak diatur dengan aman untuk lingkungan produksi!")

    # Daftarkan blueprint utama
    from . import routes 
    app.register_blueprint(routes.bp)

    # Daftarkan blueprint file manager
    from .file_manager_routes import file_manager_bp
    app.register_blueprint(file_manager_bp)

    # Daftarkan blueprint prompt template manager
    from .prompt_template_routes import prompt_template_bp
    app.register_blueprint(prompt_template_bp)

    # Daftarkan blueprint enhanced processing
    from .enhanced_routes import enhanced_bp
    app.register_blueprint(enhanced_bp)

    # Pendaftaran Blueprint Puter AI dan impor terkait telah dihapus 
    # karena fungsionalitasnya diintegrasikan ke main.js dan routes.py utama,
    # atau dihapus jika diputuskan untuk tidak menggunakan rute terpisah.


    with app.app_context():
        print("Menjalankan initial setup (memastikan direktori media & data)...")
        ensure_media_dirs() 
        # Pemanggilan ensure_puter_media_dirs_specific() juga dihapus
        # ensure_puter_media_dirs_specific() 
        print("Memuat/menginisialisasi template prompt...")
        load_prompt_templates() 
        print("Initial setup selesai.")
    
    return app