import math
import io
import base64
import smtplib
from email.mime.text import MIMEText

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fpdf import FPDF
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file

app = Flask(__name__)
app.secret_key = 'j350z271123r'  # Clave de seguridad para el login

# Configuración de sesión (para mantener el login activo)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

# -------------------------------------------------------------------------
# Función para enviar reporte de error por correo
# -------------------------------------------------------------------------
def enviar_reporte_error(mensaje):
    """
    Envía un correo electrónico con el reporte de error.
    Configura los datos SMTP con tus credenciales reales.
    """
    destinatario = "castilloreyesgabriel4@gmail.com"  # Donde se recibirán los reportes
    asunto = "Reporte de Error - Instant Math Solver"
    
    # Configuración SMTP (reemplaza estos datos por los tuyos)
    smtp_server = "castilloreyesgabriel4@gmail.com"   # Ej: "smtp.gmail.com"
    smtp_port = 465                  # Puerto SMTP
    correo_origen = "castilloreyesgabriel4@gmail.com"      # Ej: "tu_correo@gmail.com"
    password = "fjgf igtf rxmq usxc"         # Contraseña o "Contraseña de Aplicación"
    
    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = correo_origen
    msg["To"] = destinatario
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(correo_origen, password)
            server.sendmail(correo_origen, destinatario, msg.as_string())
    except Exception as e:
        print(f"Error al enviar reporte: {e}")

# -------------------------------------------------------------------------
# Funciones de cálculo y graficado
# -------------------------------------------------------------------------
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
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b)
    return datos

def distance_points(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def angle_between_lines(ang1, ang2):
    diff = abs(ang1 - ang2)
    if diff > 90:
        diff = 180 - diff
    return diff

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

def graficarRectaUnica(a, b, c, x_min=-10, x_max=10, y_min=-10, y_max=10):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(x_min, x_max, 400)
    
    def get_y(a, b, c, x_array):
         return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    y = get_y(a, b, c, x_vals)
    if y is not None:
         plt.plot(x_vals, y, label=f"{a}x + {b}y + {c} = 0", color="purple")
    else:
         try:
             x_const = -c / a
             plt.axvline(x_const, color="purple", label=f"x = {x_const:.2f}")
         except ZeroDivisionError:
             pass
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de la Recta")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.gca().set_aspect("equal", adjustable="box")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

def generar_pdf_resultado(textos):
    """
    Genera un PDF con las líneas de texto en la lista 'textos'.
    Devuelve un objeto BytesIO con el PDF generado o None en caso de error.
    """
    pdf = FPDF()
    try:
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Resultados - Instant Math Solver", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        for linea in textos:
            pdf.cell(0, 10, linea, ln=True)
        pdf.ln(10)
        pdf.cell(0, 10, "Exportado desde Instant Math Solver", ln=True, align="C")
    except Exception as e:
        print(f"Error al generar PDF: {e}")
        return None

    mem = io.BytesIO()
    try:
        pdf.output(mem)
    except Exception as e:
        print(f"Error al escribir PDF: {e}")
        return None
    mem.seek(0)
    return mem

# -------------------------------------------------------------------------
# Rutas de la aplicación
# -------------------------------------------------------------------------

# Para evitar errores en peticiones HEAD, se incluye el método HEAD en estas rutas.
@app.route("/login", methods=["GET", "POST", "HEAD"], endpoint="login")
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "alumno" and password == "amrd":
            session["logged_in"] = True
            session["user"] = username
            return redirect(url_for("index"))
        else:
            flash("Usuario o contraseña incorrectos, intente de nuevo.")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/logout", methods=["GET", "HEAD"], endpoint="logout")
def logout():
    session.pop("logged_in", None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))

# -------------------------------------------------------------------------
# Resolver dos ecuaciones
# -------------------------------------------------------------------------
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
            flash("Por favor ingresa valores numéricos válidos.")
            return render_template("index.html")
        
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
        
        angulo_entre_rectas = angle_between_lines(ang1, ang2)
        
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_min, x_max, y_min, y_max)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        distancia_interseccion_origen = None
        if resultado["tipo"] == "interseccion" and resultado["punto"]:
            distancia_interseccion_origen = distance_points(resultado["punto"], (0, 0))
        
        # Guardar datos en sesión para exportar PDF
        session["export_data"] = {
            "a1": a1, "b1": b1, "c1": c1,
            "a2": a2, "b2": b2, "c2": c2,
            "resultado": resultado,
            "datos1": datos1,
            "datos2": datos2,
            "comp_pendiente": comp_pendiente,
            "comp_inclinacion": comp_inclinacion,
            "angulo_entre_rectas": angulo_entre_rectas,
            "distancia_interseccion_origen": distancia_interseccion_origen
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

# -------------------------------------------------------------------------
# Resolver una sola ecuación
# -------------------------------------------------------------------------
@app.route("/single", methods=["GET", "POST"])
def single():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            a = float(request.form["a"])
            b = float(request.form["b"])
            c = float(request.form["c"])
        except ValueError:
            flash("Por favor ingresa valores numéricos válidos.")
            return render_template("single.html")
        
        try:
            x_min = float(request.form.get("x_min", -10))
            x_max = float(request.form.get("x_max", 10))
            y_min = float(request.form.get("y_min", -10))
            y_max = float(request.form.get("y_max", 10))
        except ValueError:
            x_min, x_max, y_min, y_max = -10, 10, -10, 10
        
        datos = calcularDatosRecta(a, b, c)
        buf = graficarRectaUnica(a, b, c, x_min, x_max, y_min, y_max)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        session["export_data_single"] = {
            "a": a, "b": b, "c": c,
            "datos": datos
        }
        
        return render_template("single.html", datos=datos, grafico=grafico)
    return render_template("single.html")

# -------------------------------------------------------------------------
# Exportar PDF para 2 ecuaciones
# -------------------------------------------------------------------------
@app.route("/export/pdf")
def export_pdf():
    export_data = session.get("export_data")
    if not export_data:
        flash("No hay datos para exportar.")
        return redirect(url_for("index"))
    
    textos = []
    textos.append(f"Recta 1: {export_data['a1']}x + {export_data['b1']}y + {export_data['c1']} = 0")
    textos.append(f"Recta 2: {export_data['a2']}x + {export_data['b2']}y + {export_data['c2']} = 0")
    textos.append(f"Tipo de solución: {export_data['resultado']['tipo']}")
    if export_data["resultado"]["punto"]:
        textos.append(f"Punto de intersección: {export_data['resultado']['punto']}")
    textos.append(f"Pendiente Recta 1: {export_data['datos1']['pendiente']}")
    textos.append(f"Pendiente Recta 2: {export_data['datos2']['pendiente']}")
    textos.append(f"Ángulo Recta 1: {export_data['datos1']['anguloConEjeX']}°")
    textos.append(f"Ángulo Recta 2: {export_data['datos2']['anguloConEjeX']}°")
    textos.append(f"Ángulo entre rectas: {export_data['angulo_entre_rectas']}°")
    if export_data["distancia_interseccion_origen"] is not None:
        textos.append(f"Distancia intersección - origen: {export_data['distancia_interseccion_origen']}")
    
    pdf_io = generar_pdf_resultado(textos)
    if pdf_io is None:
        flash("Error al generar el PDF.")
        return redirect(url_for("index"))
    return send_file(pdf_io, mimetype="application/pdf", as_attachment=True, download_name="resultados.pdf")

# -------------------------------------------------------------------------
# Exportar PDF para ecuación única
# -------------------------------------------------------------------------
@app.route("/export_single/pdf")
def export_pdf_single():
    export_data = session.get("export_data_single")
    if not export_data:
        flash("No hay datos para exportar.")
        return redirect(url_for("single"))
    
    textos = []
    textos.append(f"Ecuación: {export_data['a']}x + {export_data['b']}y + {export_data['c']} = 0")
    textos.append(f"Pendiente: {export_data['datos']['pendiente']}")
    textos.append(f"Ángulo con eje X: {export_data['datos']['anguloConEjeX']}°")
    textos.append(f"Distancia al origen: {export_data['datos']['distanciaAlOrigen']}")
    
    pdf_io = generar_pdf_resultado(textos)
    if pdf_io is None:
        flash("Error al generar el PDF.")
        return redirect(url_for("single"))
    return send_file(pdf_io, mimetype="application/pdf", as_attachment=True, download_name="resultados_unica.pdf")

# -------------------------------------------------------------------------
# Reporte de Errores
# -------------------------------------------------------------------------
@app.route("/error_report", methods=["GET", "POST"])
def error_report():
    if request.method == "POST":
        mensaje = request.form.get("mensaje", "")
        if mensaje:
            enviar_reporte_error(mensaje)
            flash("¡Gracias por reportar el error!")
        else:
            flash("Debes escribir un mensaje.")
        return redirect(url_for("index"))
    return render_template("error_report.html")

# -------------------------------------------------------------------------
# Donaciones
# -------------------------------------------------------------------------
@app.route("/donations")
def donations():
    return render_template("donations.html")

if __name__ == "__main__":
    app.run(debug=True)
