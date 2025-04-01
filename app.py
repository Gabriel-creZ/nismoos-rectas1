import math
import io
import base64
import smtplib
from email.mime.text import MIMEText

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'j350z271123r'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_TYPE'] = 'filesystem'

def enviar_reporte_error(mensaje):
    destinatario = "castilloreyesgabriel4@gmail.com"
    asunto = "Reporte de Error - Instant Math Solver"
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    correo_origen = "castilloreyesgabriel4@gmail.com"
    password = "wkiqrqkcvhoirdyr"
    
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
    datos["pendiente"] = None if abs(b) < 1e-14 else -a / b
    datos["interseccionX"] = None if abs(a) < 1e-14 else -c / a
    datos["interseccionY"] = None if abs(b) < 1e-14 else -c / b
    datos["anguloConEjeX"] = 90.0 if datos["pendiente"] is None else math.degrees(math.atan(datos["pendiente"]))
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b)
    return datos

def graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_min=-10, x_max=10, y_min=-10, y_max=10):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(x_min, x_max, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    y1 = get_y(a1, b1, c1, x_vals)
    if y1 is not None:
        plt.plot(x_vals, y1, label=f"R1: {a1}x + {b1}y + {c1} = 0", color="darkorange")
    else:
        x_const = -c1 / a1
        plt.axvline(x_const, color='darkorange', label=f"R1: x = {x_const:.2f}")
    
    y2 = get_y(a2, b2, c2, x_vals)
    if y2 is not None:
        plt.plot(x_vals, y2, label=f"R2: {a2}x + {b2}y + {c2} = 0", color="teal")
    else:
        x_const = -c2 / a2
        plt.axvline(x_const, color='teal', label=f"R2: x = {x_const:.2f}")
    
    if resultado["tipo"] == "interseccion" and resultado["punto"]:
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
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close()
    return buf

def graficarRectaUnica(a, b, c, x_min=-10, x_max=10, y_min=-10, y_max=10):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(x_min, x_max, 400)
    
    y = (-a * x_vals - c) / b if abs(b) > 1e-14 else None
    if y is not None:
        plt.plot(x_vals, y, label=f"{a}x + {b}y + {c} = 0", color="purple")
    else:
        x_const = -c / a
        plt.axvline(x_const, color="purple", label=f"x = {x_const:.2f}")
    
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
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close()
    return buf

@app.route("/login", methods=["GET", "POST"])
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

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            a1 = float(request.form["a1"].strip())
            b1 = float(request.form["b1"].strip())
            c1 = float(request.form["c1"].strip())
            a2 = float(request.form["a2"].strip())
            b2 = float(request.form["b2"].strip())
            c2 = float(request.form["c2"].strip())
            
            x_min = float(request.form.get("x_min", "-10").strip())
            x_max = float(request.form.get("x_max", "10").strip())
            y_min = float(request.form.get("y_min", "-10").strip())
            y_max = float(request.form.get("y_max", "10").strip())
        except ValueError as e:
            flash("Error: Asegúrate de ingresar solo números válidos (ej. 3, -2.5, 0.7)")
            return render_template("index.html")
        
        resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
        datos1 = calcularDatosRecta(a1, b1, c1)
        datos2 = calcularDatosRecta(a2, b2, c2)
        
        pendiente1 = datos1["pendiente"] if datos1["pendiente"] is not None else float('inf')
        pendiente2 = datos2["pendiente"] if datos2["pendiente"] is not None else float('inf')
        
        comp_pendiente = "🔥 Ambas rectas tienen la misma pendiente."
        if abs(pendiente1) > abs(pendiente2):
            comp_pendiente = f"🔥 La recta 1 tiene la mayor pendiente: {datos1['pendiente']}"
        elif abs(pendiente2) > abs(pendiente1):
            comp_pendiente = f"🔥 La recta 2 tiene la mayor pendiente: {datos2['pendiente']}"
        
        ang1 = datos1["anguloConEjeX"]
        ang2 = datos2["anguloConEjeX"]
        angulo_entre_rectas = abs(ang1 - ang2) if abs(ang1 - ang2) <= 90 else 180 - abs(ang1 - ang2)
        
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_min, x_max, y_min, y_max)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        return render_template("resultado.html",
                           resultado=resultado,
                           datos1=datos1,
                           datos2=datos2,
                           comp_pendiente=comp_pendiente,
                           angulo_entre_rectas=angulo_entre_rectas,
                           grafico=grafico)
    return render_template("index.html")

@app.route("/single", methods=["GET", "POST"])
def single():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        try:
            a = float(request.form["a"].strip())
            b = float(request.form["b"].strip())
            c = float(request.form["c"].strip())
            
            x_min = float(request.form.get("x_min", "-10").strip())
            x_max = float(request.form.get("x_max", "10").strip())
            y_min = float(request.form.get("y_min", "-10").strip())
            y_max = float(request.form.get("y_max", "10").strip())
        except ValueError as e:
            flash("Error: Asegúrate de ingresar solo números válidos (ej. 3, -2.5, 0.7)")
            return render_template("single.html")
        
        datos = calcularDatosRecta(a, b, c)
        buf = graficarRectaUnica(a, b, c, x_min, x_max, y_min, y_max)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        return render_template("single.html", datos=datos, grafico=grafico)
    return render_template("single.html")

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

@app.route("/donations")
def donations():
    return render_template("donations.html")

if __name__ == "__main__":
    app.run(debug=False)