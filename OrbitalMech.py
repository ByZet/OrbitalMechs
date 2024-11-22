import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests
import math
import numpy as np
from datetime import datetime, timedelta


def derece(x):
    
    return x * 180 / math.pi

def turev(E, e):
    return 1.0 - e * np.cos(E)

def theta(E, e):
    return 2 * math.atan(math.sqrt((1 + e) / (1 - e)) * math.tan(E / 2))

def fetch_data(target, date_range):
    try:
        url = "https://ssd.jpl.nasa.gov/api/horizons.api"
        if '/' in date_range:
            start_date, end_date = date_range.split('/')
        else:
            start_date = date_range
            date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        
        result_box.insert(tk.END, f"Başlangıç tarihi: {start_date}\n")
        result_box.insert(tk.END, f"Bitiş tarihi: {end_date}\n")
        
        params = {
            "format": "text",
            "COMMAND": target,
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "ELEMENTS",
            "CENTER": "@10",
            "START_TIME": start_date,
            "STOP_TIME": end_date,
            "STEP_SIZE": "1d",
            "REF_PLANE": "ECLIPTIC",
            "REF_SYSTEM": "J2000",
            "TP_TYPE": "ABSOLUTE",
            "ELEM_LABELS": "YES",
            "CSV_FORMAT": "NO",
            "OBJ_DATA": "YES",
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result_box.insert(tk.END, "API'den veri başarıyla alındı.\n")
            return response.text
        else:
            result_box.insert(tk.END, f"API Hatası: {response.status_code}\n")
            result_box.insert(tk.END, f"Hata Mesajı: {response.text}\n")
            return None
    except Exception as e:
        result_box.insert(tk.END, f"Veri alma hatası: {str(e)}\n")
        return None


def parse_table(data):
    start_tag = "$$SOE"
    end_tag = "$$EOE"
    table_start = data.find(start_tag)
    table_end = data.find(end_tag)

    if table_start == -1 or table_end == -1:
        result_box.insert(tk.END, f"API Yanıtı:\n{data}\n")
        raise ValueError("Tablo verileri bulunamadı.")

    table_data = data[table_start + len(start_tag):table_end].strip()
    return [line for line in table_data.splitlines() if line.strip()]


def extract_values(data):
    lines = parse_table(data)
    ec = None
    ma = None
    ta = None
    
    for line in lines:
     
        if "=" not in line:
            continue
            
      
        if "EC=" in line:
            try:
                ec_part = line.split("EC=")[1].split()[0]
                ec = float(ec_part)
                result_box.insert(tk.END, f"EC = {ec:.6E}\n")
            except Exception:
                pass
                
      
        if "MA=" in line and "TA=" in line:
            try:
             
                ma_part = line.split("MA=")[1].split()[0]
                ma = float(ma_part)
                result_box.insert(tk.END, f"MA = {ma:.6E}\n")
                
             
                ta_part = line.split("TA=")[1].split()[0]
                ta = float(ta_part)
                result_box.insert(tk.END, f"TA = {ta:.6E}\n")
            except Exception:
                pass
        
      
        if ec is not None and ma is not None and ta is not None:
            break
    
    if ec is not None and ma is not None and ta is not None:
        result_box.insert(tk.END, f"\nBulunan değerler:\n")
        result_box.insert(tk.END, f"e = {ec:.6E}\n")
        result_box.insert(tk.END, f"MA = {ma:.6E}\n")
        result_box.insert(tk.END, f"TA = {ta:.6E}\n")
        return {
            "EC": ec,
            "MA": ma,
            "TA": ta
        }
    else:
        missing = []
        if ec is None: missing.append("EC")
        if ma is None: missing.append("MA")
        if ta is None: missing.append("TA")
        raise ValueError(f"Bulunamayan değerler: {', '.join(missing)}")


def get_target_name(data):
    for line in data.splitlines():
        if "Target body name:" in line:
            return line.split(":")[1].strip()
    return "Bilinmeyen Cisim"

def calculate():
    cisim = cisim_entry.get()
    tarih = tarih_entry.get()
    iterasyon = iterasyon_entry.get()

    if not cisim or not tarih or not iterasyon:
        messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
        return

    try:
        iterasyon = int(iterasyon)
        if iterasyon <= 0:
            raise ValueError("İterasyon sayısı pozitif bir tam sayı olmalıdır.")
    except ValueError:
        messagebox.showerror("Hata", "Geçerli bir iterasyon sayısı girin.")
        return

    data = fetch_data(cisim, tarih)
    if data:
        try:
            parsed_values = extract_values(data)
            cisim_adı = get_target_name(data)
            
            e = parsed_values["EC"]
            MA = math.radians(parsed_values["MA"])
            TA = parsed_values["TA"]

            E = MA
            for i in range(iterasyon):
                F = E - e * np.sin(E) - MA
                dF = turev(E, e)
                E = E - F / dF
                result_box.insert(tk.END, f"İterasyon {i+1}:\nE = {math.degrees(E):.6f} derece\n")

            theta_rad = theta(E, e)
            theta_deg = derece(theta_rad)
            if theta_deg <= 0:
                theta_deg += 360

            mutlak_hata = abs(theta_deg - TA)
            result_text.set(
                f"Cisim: {cisim_adı}\n"
                f"Tarih: {tarih}\n"
                f"MA = {parsed_values['MA']:.6E}\n"
                f"e = {e:.6E}\n"
                f"TA = {TA:.6E}\n"
                f"θ = {theta_deg:.6f} derece\n"
                f"Mutlak Hata: {mutlak_hata:.6f}"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama sırasında bir hata oluştu: {e}")
            result_box.insert(tk.END, f"Hata detayları: {str(e)}\n")




root = tk.Tk()
root.title("Yörünge Mekaniği")
root.geometry("600x500")
root.configure(bg="#1E1E1E")  


header_frame = tk.Frame(root, bg="#1E1E1E")
header_frame.pack(pady=10)

header_label = tk.Label(header_frame, text="Yörünge Mekaniği", font=("Helvetica", 16, "bold"), fg="white", bg="#1E1E1E")
header_label.pack()

description_label = tk.Label(header_frame, text="Bu program, belirli bir cisim için astronomik hesaplamalar yapar.", font=("Helvetica", 10), fg="white", bg="#1E1E1E")
description_label.pack()


input_frame = tk.Frame(root, bg="#1E1E1E")
input_frame.pack(pady=10)

cisim_label = tk.Label(input_frame, text="Cisim:", font=("Helvetica", 12), fg="white", bg="#1E1E1E")
cisim_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
cisim_entry = tk.Entry(input_frame, width=40, font=("Helvetica", 12), relief="flat", highlightbackground="white", highlightthickness=1)
cisim_entry.grid(row=0, column=1, padx=5, pady=5)

tarih_label = tk.Label(input_frame, text="Tarih (YYYY-MM-DD):", font=("Helvetica", 12), fg="white", bg="#1E1E1E")
tarih_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
tarih_entry = tk.Entry(input_frame, width=40, font=("Helvetica", 12), relief="flat", highlightbackground="white", highlightthickness=1)
tarih_entry.grid(row=1, column=1, padx=5, pady=5)

iterasyon_label = tk.Label(input_frame, text="İterasyon Sayısı:", font=("Helvetica", 12), fg="white", bg="#1E1E1E")
iterasyon_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
iterasyon_entry = tk.Entry(input_frame, width=40, font=("Helvetica", 12), relief="flat", highlightbackground="white", highlightthickness=1)
iterasyon_entry.grid(row=2, column=1, padx=5, pady=5)


button_frame = tk.Frame(root, bg="#1E1E1E")
button_frame.pack(pady=10)

calculate_button = tk.Button(button_frame, text="Hesapla", command=calculate, font=("Helvetica", 12, "bold"), bg="#00A8E8", fg="white", activebackground="#005F8F", relief="flat", width=20)
calculate_button.pack()

result_frame = tk.Frame(root, bg="#1E1E1E")
result_frame.pack(pady=10)

result_label = tk.Label(result_frame, text="Sonuçlar:", font=("Helvetica", 12, "bold"), fg="white", bg="#1E1E1E")
result_label.pack()

result_text = tk.StringVar()
result_output = tk.Label(result_frame, textvariable=result_text, justify="left", font=("Helvetica", 10), fg="white", bg="#1E1E1E")
result_output.pack(pady=5)

result_box = scrolledtext.ScrolledText(result_frame, width=70, height=15, font=("Courier", 10), bg="#2C2C2C", fg="white", relief="flat", insertbackground="white")
result_box.pack(pady=10)

root.mainloop()