import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import os
from datetime import datetime

Base = declarative_base()

class Tarea(Base):
    __tablename__ = 'tareas'
    id = Column(Integer, primary_key=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    completada = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.now)

class AplicacionGestorTareas:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Gestor de Tareas")
        self.raiz.geometry("1000x600")
        self.raiz.configure(bg="#f5f5f5")

        self.COLORES = {
            "primario": "#2c3e50",
            "secundario": "#34495e", 
            "acento": "#3498db",
            "exito": "#2ecc71",
            "advertencia": "#f1c40f",
            "error": "#e74c3c",
            "texto": "#ecf0f1",
            "fondo": "#f5f5f5"
        }

        try:
            self.engine = create_engine('sqlite:///tareas.db')
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", 
                               f"No se pudo conectar a la base de datos: {str(e)}")

        self.crear_interfaz()
        self.configurar_estilos()
        self.actualizar_lista_tareas()

    def crear_interfaz(self):
        self.marco_principal = tk.Frame(self.raiz, bg=self.COLORES["fondo"])
        self.marco_principal.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        titulo = tk.Label(self.marco_principal,
                         text="Gestión de Tareas Premium",
                         font=("Helvetica", 24, "bold"),
                         bg=self.COLORES["fondo"],
                         fg=self.COLORES["primario"])
        titulo.pack(pady=10)

        marco_form = tk.LabelFrame(self.marco_principal,
                                 text="Nueva Tarea",
                                 font=("Helvetica", 12, "bold"),
                                 bg=self.COLORES["fondo"],
                                 fg=self.COLORES["primario"])
        marco_form.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(marco_form, text="Título:", bg=self.COLORES["fondo"],
                font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.entrada_titulo = tk.Entry(marco_form, width=40, font=("Helvetica", 10))
        self.entrada_titulo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(marco_form, text="Descripción:", bg=self.COLORES["fondo"],
                font=("Helvetica", 10, "bold")).grid(row=1, column=0, padx=5, pady=5)
        self.entrada_descripcion = tk.Text(marco_form, width=40, height=3, font=("Helvetica", 10))
        self.entrada_descripcion.grid(row=1, column=1, padx=5, pady=5)

        marco_botones = tk.Frame(self.marco_principal, bg=self.COLORES["fondo"])
        marco_botones.pack(pady=10)

        botones = [
            ("➕ Agregar", self.COLORES["exito"], self.agregar_tarea),
            ("✓ Completar", self.COLORES["acento"], self.marcar_completada),
            ("🗑️ Eliminar", self.COLORES["error"], self.eliminar_tarea),
            ("💾 Guardar", self.COLORES["primario"], self.guardar_tareas),
            ("📂 Cargar", self.COLORES["secundario"], self.cargar_tareas)
        ]

        for texto, color, comando in botones:
            btn = tk.Button(marco_botones, text=texto, bg=color, fg="white",
                          font=("Helvetica", 10, "bold"), width=15, command=comando,
                          relief="flat", cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.aclarar_color(b.cget("bg"))))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))

        self.crear_tabla()

    def crear_tabla(self):
        marco_tabla = tk.LabelFrame(self.marco_principal, text="Mis Tareas",
                                  font=("Helvetica", 12, "bold"),
                                  bg=self.COLORES["fondo"],
                                  fg=self.COLORES["primario"])
        marco_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columnas = ("ID", "Título", "Descripción", "Estado")
        self.tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")
        
        anchos = [50, 200, 300, 100]
        for col, ancho in zip(columnas, anchos):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=ancho)

        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tabla.pack(fill=tk.BOTH, expand=True)

    def configurar_estilos(self):
        style = ttk.Style()
        style.configure("Treeview",
                      background="transparent",
                      foreground="#0a0a0a",
                      rowheight=25,
                      fieldbackground="transparent",
                      font=("Helvetica", 10))
        style.configure("Treeview.Heading",
                      font=("Helvetica", 10, "bold"),
                      background="#1e272e",
                      foreground="#0a0a0a")
        
        style.map('Treeview',
                  background=[('selected', '#0097e6')],
                  foreground=[('selected', 'black')])

    def aclarar_color(self, color_hex):
        rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb_aclarado = tuple(min(255, c + 20) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb_aclarado)

    def actualizar_lista_tareas(self):
        try:
            for item in self.tabla.get_children():
                self.tabla.delete(item)
                
            tareas = self.session.query(Tarea).all()
            for tarea in tareas:
                estado = "Completada" if tarea.completada else "Pendiente"
                self.tabla.insert("", tk.END, values=(tarea.id, tarea.titulo, tarea.descripcion, estado))
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar la lista: {str(e)}")

    def agregar_tarea(self):
        try:
            titulo = self.entrada_titulo.get()
            descripcion = self.entrada_descripcion.get("1.0", tk.END)
            
            if not titulo:
                messagebox.showerror("Error", "El título es obligatorio")
                return
                
            nueva_tarea = Tarea(titulo=titulo, descripcion=descripcion, completada=False)
            self.session.add(nueva_tarea)
            self.session.commit()
            
            self.limpiar_campos()
            self.actualizar_lista_tareas()
            messagebox.showinfo("Éxito", "Tarea agregada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar tarea: {str(e)}")

    def marcar_completada(self):
        try:
            seleccion = self.tabla.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Por favor seleccione una tarea")
                return
                
            item = self.tabla.item(seleccion[0])
            id_tarea = item['values'][0]
            
            tarea = self.session.query(Tarea).filter_by(id=id_tarea).first()
            if tarea:
                tarea.completada = not tarea.completada
                self.session.commit()
                self.actualizar_lista_tareas()
        except Exception as e:
            messagebox.showerror("Error", f"Error al marcar tarea: {str(e)}")

    def eliminar_tarea(self):
        try:
            seleccion = self.tabla.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Por favor seleccione una tarea")
                return
                
            if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta tarea?"):
                item = self.tabla.item(seleccion[0])
                id_tarea = item['values'][0]
                
                tarea = self.session.query(Tarea).filter_by(id=id_tarea).first()
                if tarea:
                    self.session.delete(tarea)
                    self.session.commit()
                    self.actualizar_lista_tareas()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar tarea: {str(e)}")

    def guardar_tareas(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                tareas = self.session.query(Tarea).all()
                datos = []
                for tarea in tareas:
                    datos.append({
                        'titulo': tarea.titulo,
                        'descripcion': tarea.descripcion,
                        'completada': tarea.completada
                    })
                with open(filename, 'w') as f:
                    json.dump(datos, f)
                messagebox.showinfo("Éxito", "Tareas guardadas correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar tareas: {str(e)}")

    def cargar_tareas(self):
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r') as f:
                    datos = json.load(f)
                for tarea_data in datos:
                    nueva_tarea = Tarea(
                        titulo=tarea_data['titulo'],
                        descripcion=tarea_data['descripcion'],
                        completada=tarea_data['completada']
                    )
                    self.session.add(nueva_tarea)
                self.session.commit()
                self.actualizar_lista_tareas()
                messagebox.showinfo("Éxito", "Tareas cargadas correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tareas: {str(e)}")

    def limpiar_campos(self):
        self.entrada_titulo.delete(0, tk.END)
        self.entrada_descripcion.delete(1.0, tk.END)

if __name__ == "__main__":
    try:
        raiz = tk.Tk()
        app = AplicacionGestorTareas(raiz)
        raiz.mainloop()
    except Exception as e:
        messagebox.showerror("Error Fatal", 
                           f"Error al iniciar la aplicación: {str(e)}")