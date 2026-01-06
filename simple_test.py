import customtkinter as ctk

# Schreibe Log
with open("simple_test.log", "w") as f:
    f.write("Script startet!\n")

# Erstelle GUI
app = ctk.CTk()
app.title("Test GUI")
app.geometry("400x300")

label = ctk.CTkLabel(app, text="GUI FUNKTIONIERT!", font=("Arial", 24))
label.pack(pady=50)

button = ctk.CTkButton(app, text="Beenden", command=app.quit)
button.pack(pady=20)

with open("simple_test.log", "a") as f:
    f.write("GUI erstellt, starte mainloop\n")

app.mainloop()

with open("simple_test.log", "a") as f:
    f.write("GUI beendet\n")

