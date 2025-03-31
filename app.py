from flask import Flask, render_template, request, redirect, url_for, session, flash
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

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
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b)
    return datos

def graficarRectas(a1, b1, c1, a2, b2, c2, resultado):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(-10, 10, 400)
    
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
    
    if resultado["tipo"] == "interseccion" and resultado["punto"] is not None:
        x_sol, y_sol = resultado["punto"]
        plt.plot(x_sol, y_sol, 'ko', label="Intersección")
    
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de las Rectas")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

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
        
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        return render_template("resultado.html",
                               resultado=resultado,
                               datos1=datos1,
                               datos2=datos2,
                               comp_pendiente=comp_pendiente,
                               comp_inclinacion=comp_inclinacion,
                               grafico=grafico)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
