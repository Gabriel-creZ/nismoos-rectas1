from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import csv
from fpdf import FPDF  # Para exportar a PDF

app = Flask(__name__)
app.secret_key = 'j350z271123r'  # Clave de seguridad para el login

# Configuración de sesión (para mantener el login activo)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

# --- Funciones de cálculo y graficado ---

def resolverSistema(a1, b1, c1, a2, b2, c2):
    det = a1 * b2 - a2 * b1
    resultado = {"det": det, "tipo": None, "punto": None}
    if abs(det) < 1e-14:
        proporcion = None
        if abs(a2) > 1e-14:
            proporcion = a1 / a2
        elif abs(b2) > 1e-14:
            proporcion = b1 / b2
        elif abs(c2) > 1e-14:
            proporcion = c1 / c2
        
        if proporcion is not None:
            check_b = abs(b1 - proporcion * b2) < 1e-9
            check_c = abs(c1 - proporcion * c2) < 1e-9
            if check_b and check_c:
                resultado["tipo"] = "coincidentes"
            else:
                resultado["tipo"] = "paralelas"
        else:
            resultado["tipo"] = "indefinido"
    else:
        det_x = (-c1) * b2 - (-c2) * b1
        det_y = a1 * (-c2) - a2 * (-c1)
        x_sol = det_x / det
        y_sol = det_y / det
        resultado["tipo"] = "interseccion"
        resultado["punto"] = (x_sol, y_sol)
    return resultado

def calcularDatosRecta(a, b, c):
    datos = {}
    if abs(b) < 1e-14:
        datos["pendiente"] = None
    else:
        datos["pendiente"] = -a / b
    datos["interseccionX"] = None if abs(a) < 1e-14 else -c / a
    datos["interseccionY"] = None if abs(b) < 1e-14 else -c / b
    if datos["pendiente"] is None:
        datos["anguloConEjeX"] = 90.0
    else:
        datos["anguloConEjeX"] = math.degrees(math.atan(datos["pendiente"]))
    # Distancia desde el origen a la recta
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b)
    return datos

# Nueva función: Convertir de forma general a pendiente-intersección
def general_to_slope(a, b, c):
    """
    Convierte la ecuación general Ax + By + C = 0 a la forma pendiente-intersección (y = mx + k).
    Retorna (m, k). Si la recta es vertical, retorna (None, None).
    """
    if abs(b) < 1e-14:
        return None, None  # Recta vertical, no se puede expresar en forma y = mx + k
    m = -a / b
    k = -c / b
    return m, k

# Nueva función: Calcular la distancia entre dos puntos
def distance_points(p1, p2):
    """
    Calcula la distancia euclidiana entre dos puntos p1 y p2.
    Cada punto es una tupla (x, y).
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_min=-10, x_max=10, y_min=-10, y_max=10):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(x_min, x_max, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    y1 = get_y(a1, b1, c1, x_vals)
    if y1 is not None:
        plt.plot(x_vals, y1, label=f"R1: {a1}x + {b1}y + {c1} = 0", color="darkorange")
    else:
        try:
            x_const = -c1 / a1
            plt.axvline(x_const, color='darkorange', label=f"R1: x = {x_const:.2f}")
        except ZeroDivisionError:
            pass
    
    y2 = get_y(a2, b2, c2, x_vals)
    if y2 is not None:
        plt.plot(x_vals, y2, label=f"R2: {a2}x + {b2}y + {c2} = 0", color="teal")
    else:
        try:
            x_const = -c2 / a2
            plt.axvline(x_const, color='teal', label=f"R2: x = {x_const:.2f}")
        except ZeroDivisionError:
            pass
    
    if resultado["tipo"] == "interseccion" and resultado["punto"] is not None:
        x_sol, y_sol = resultado["punto"]
        plt.plot(x_sol, y_sol, 'ko', label="Intersección")
    
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de las Rectas")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.gca().set_aspect('equal', adjustable='box')
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# Nueva función: Calcular el ángulo entre dos rectas usando sus pendientes o ángulos con el eje X
def angle_between_lines(ang1, ang2):
    """
    Calcula el ángulo mínimo entre dos rectas dados sus ángulos con el eje X.
    """
    diff = abs(ang1 - ang2)
    if diff > 90:
        diff = 180 - diff
    return diff

# --- Rutas para login y autenticación ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Validación con usuario "alumno" y contraseña "amrd"
        if username == "alumno" and password == "amrd":
            session["logged_in"] = True
            session["user"] = username
            return redirect(url_for("index"))
        else:
            flash("Usuario o contraseña incorrectos, intente de nuevo.")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))

# --- Ruta principal (index) ---

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            a1 = float(request.form["a1"])
            b1 = float(request.form["b1"])
            c1 = float(request.form["c1"])
            a2 = float(request.form["a2"])
            b2 = float(request.form["b2"])
            c2 = float(request.form["c2"])
        except ValueError:
            return render_template("index.html", error="Por favor ingresa valores numéricos válidos.")
        
        # Manejo opcional del rango de la gráfica
        try:
            x_min = float(request.form.get("x_min", -10))
            x_max = float(request.form.get("x_max", 10))
            y_min = float(request.form.get("y_min", -10))
            y_max = float(request.form.get("y_max", 10))
        except ValueError:
            x_min, x_max, y_min, y_max = -10, 10, -10, 10
        
        resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
        datos1 = calcularDatosRecta(a1, b1, c1)
        datos2 = calcularDatosRecta(a2, b2, c2)
        
        # Comparación de pendientes e inclinaciones
        pendiente1 = datos1["pendiente"] if datos1["pendiente"] is not None else float('inf')
        pendiente2 = datos2["pendiente"] if datos2["pendiente"] is not None else float('inf')
        if abs(pendiente1) > abs(pendiente2):
            comp_pendiente = f"🔥 La recta 1 tiene la mayor pendiente: {datos1['pendiente']}"
        elif abs(pendiente2) > abs(pendiente1):
            comp_pendiente = f"🔥 La recta 2 tiene la mayor pendiente: {datos2['pendiente']}"
        else:
            comp_pendiente = "🔥 Ambas rectas tienen la misma pendiente."
        
        ang1 = datos1["anguloConEjeX"]
        ang2 = datos2["anguloConEjeX"]
        if ang1 > ang2:
            comp_inclinacion = f"🌟 La recta 1 tiene mayor inclinación: {ang1}°"
        elif ang2 > ang1:
            comp_inclinacion = f"🌟 La recta 2 tiene mayor inclinación: {ang2}°"
        else:
            comp_inclinacion = "🌟 Ambas rectas tienen la misma inclinación."
        
        # Cálculo del ángulo entre las rectas
        angulo_entre_rectas = angle_between_lines(ang1, ang2)
        
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_min, x_max, y_min, y_max)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        # Si hay punto de intersección, calcular distancia entre él y el origen
        distancia_interseccion_origen = None
        if resultado["tipo"] == "interseccion" and resultado["punto"]:
            distancia_interseccion_origen = distance_points(resultado["punto"], (0, 0))
        
        # Guardamos los datos para exportar (CSV/PDF)
        session["export_data"] = {
            "a1": a1, "b1": b1, "c1": c1,
            "a2": a2, "b2": b2, "c2": c2,
            "resultado": resultado,
            "datos1": datos1,
            "datos2": datos2,
            "comp_pendiente": comp_pendiente,
            "comp_inclinacion": comp_inclinacion,
            "angulo_entre_rectas": angulo_entre_rectas,
            "distancia_interseccion_origen": distancia_interseccion_origen,
            "grafico": grafico,
            "x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max
        }
        
        return render_template("resultado.html",
                               resultado=resultado,
                               datos1=datos1,
                               datos2=datos2,
                               comp_pendiente=comp_pendiente,
                               comp_inclinacion=comp_inclinacion,
                               angulo_entre_rectas=angulo_entre_rectas,
                               distancia_interseccion_origen=distancia_interseccion_origen,
                               grafico=grafico)
    return render_template("index.html")

# Ruta para exportar resultados en CSV
@app.route("/export/csv")
def export_csv():
    export_data = session.get("export_data")
    if not export_data:
        flash("No hay datos para exportar.")
        return redirect(url_for("index"))
    
    # Creamos un CSV en memoria
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Escribir encabezados y datos
    cw.writerow(["Parámetro", "Valor"])
    cw.writerow(["a1", export_data["a1"]])
    cw.writerow(["b1", export_data["b1"]])
    cw.writerow(["c1", export_data["c1"]])
    cw.writerow(["a2", export_data["a2"]])
    cw.writerow(["b2", export_data["b2"]])
    cw.writerow(["c2", export_data["c2"]])
    cw.writerow(["Tipo de solución", export_data["resultado"]["tipo"]])
    if export_data["resultado"]["punto"]:
        cw.writerow(["Punto de intersección", f"{export_data['resultado']['punto']}"])
    cw.writerow(["Pendiente Recta 1", export_data["datos1"]["pendiente"]])
    cw.writerow(["Pendiente Recta 2", export_data["datos2"]["pendiente"]])
    cw.writerow(["Ángulo Recta 1 (°)", export_data["datos1"]["anguloConEjeX"]])
    cw.writerow(["Ángulo Recta 2 (°)", export_data["datos2"]["anguloConEjeX"]])
    cw.writerow(["Ángulo entre rectas (°)", export_data["angulo_entre_rectas"]])
    if export_data["distancia_interseccion_origen"] is not None:
        cw.writerow(["Distancia entre la intersección y el origen", export_data["distancia_interseccion_origen"]])
    
    si.seek(0)
    mem = io.BytesIO()
    mem.write(si.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, attachment_filename="resultados.csv")

# Ruta para exportar resultados en PDF
@app.route("/export/pdf")
def export_pdf():
    export_data = session.get("export_data")
    if not export_data:
        flash("No hay datos para exportar.")
        return redirect(url_for("index"))
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Resultados - Resolución de Rectas", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    # Datos de entrada
    pdf.cell(0, 10, f"Recta 1: {export_data['a1']}x + {export_data['b1']}y + {export_data['c1']} = 0", ln=True)
    pdf.cell(0, 10, f"Recta 2: {export_data['a2']}x + {export_data['b2']}y + {export_data['c2']} = 0", ln=True)
    pdf.ln(5)
    
    # Resultado del sistema
    pdf.cell(0, 10, f"Tipo de solución: {export_data['resultado']['tipo']}", ln=True)
    if export_data["resultado"]["punto"]:
        pdf.cell(0, 10, f"Punto de intersección: {export_data['resultado']['punto']}", ln=True)
    pdf.ln(5)
    
    # Datos de cada recta
    pdf.cell(0, 10, f"Recta 1 - Pendiente: {export_data['datos1']['pendiente']}, Ángulo: {export_data['datos1']['anguloConEjeX']}°", ln=True)
    pdf.cell(0, 10, f"Recta 2 - Pendiente: {export_data['datos2']['pendiente']}, Ángulo: {export_data['datos2']['anguloConEjeX']}°", ln=True)
    pdf.ln(5)
    
    pdf.cell(0, 10, f"Ángulo entre rectas: {export_data['angulo_entre_rectas']}°", ln=True)
    if export_data["distancia_interseccion_origen"] is not None:
        pdf.cell(0, 10, f"Distancia entre la intersección y el origen: {export_data['distancia_interseccion_origen']}", ln=True)
    
    pdf.ln(10)
    pdf.cell(0, 10, "Exportado desde Instant Math Solver", ln=True, align="C")
    
    mem = io.BytesIO()
    pdf.output(mem)
    mem.seek(0)
    return send_file(mem, mimetype="application/pdf", as_attachment=True, attachment_filename="resultados.pdf")

if __name__ == "__main__":
    app.run(debug=True)
