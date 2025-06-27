import os
from app import create_app

# Mendapatkan port dari variabel lingkungan atau menggunakan default 5000
# Ini penting untuk deployment di lingkungan seperti Render atau platform lain yang menyediakan PORT
port = int(os.environ.get('PORT', 5000))

# Membuat instance aplikasi Flask
app = create_app()

if __name__ == '__main__':
    # Menjalankan aplikasi dalam mode debug.
    # debug=True akan memberikan output error yang lebih detail di browser
    # dan me-reload server secara otomatis saat ada perubahan kode.
    # host='0.0.0.0' akan membuat server dapat diakses dari luar localhost (penting untuk deployment).
    app.run(debug=True, host='0.0.0.0', port=port)

