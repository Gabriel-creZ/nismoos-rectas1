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
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

# --- Funciones adicionales ---

def convertirFormaPendiente(a, b, c):
    """Convierte la ecuación Ax + By + C = 0 a forma pendiente-intersección (y = mx + b) si es posible."""
    if abs(b) < 1e-14:
        return "Vertical: x = {:.2f}".format(-c/a) if abs(a) > 1e-14 else "Indefinido"
    else:
        m = -a/b
        interseccion = -c/b
        return "y = {:.2f}x + {:.2f}".format(m, interseccion)

def distanciaEntrePuntos(x1, y1, x2, y2):
    """Calcula la distancia entre dos puntos."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calcularAnguloEntreRectas(m1, m2):
    """Calcula el ángulo entre dos rectas dadas sus pendientes.
    Se maneja el caso de recta vertical utilizando float('inf')."""
    if m1 == float('inf') or m2 == float('inf'):
        if m1 == float('inf') and m2 != float('inf'):
            ang = abs(90 - math.degrees(math.atan(abs(m2))))
        elif m2 == float('inf') and m1 != float('inf'):
            ang = abs(90 - math.degrees(math.atan(abs(m1))))
        else:
            ang = 0
    else:
        try:
            tan_theta = abs((m1 - m2) / (1 + m1*m2))
            ang = math.degrees(math.atan(tan_theta))
        except ZeroDivisionError:
            ang = 90.0
    return ang

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
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b) if (a != 0 or b != 0) else None
    datos["formaPendiente"] = convertirFormaPendiente(a, b, c)
    return datos

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
        resultado["distanciaOrigen"] = distanciaEntrePuntos(x_sol, y_sol, 0, 0)
    return resultado

def graficarRectas(a1, b1, c1, a2=None, b2=None, c2=None, resultado=None, rango=None):
    plt.figure(figsize=(7, 7))
    if rango:
        x_min = rango.get("x_min", -10)
        x_max = rango.get("x_max", 10)
        y_min = rango.get("y_min", -10)
        y_max = rango.get("y_max", 10)
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        x_vals = np.linspace(x_min, x_max, 400)
    else:
        x_vals = np.linspace(-10, 10, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    # Graficar Recta 1
    y1 = get_y(a1, b1, c1, x_vals)
    if y1 is not None:
        plt.plot(x_vals, y1, label=f"R1: {convertirFormaPendiente(a1, b1, c1)}", color="darkorange")
    else:
        x_const = -c1 / a1
        plt.axvline(x_const, color='darkorange', label=f"R1: x = {x_const:.2f}")
    
    # Graficar Recta 2 si se proporcionan
    if a2 is not None and b2 is not None and c2 is not None:
        y2 = get_y(a2, b2, c2, x_vals)
        if y2 is not None:
            plt.plot(x_vals, y2, label=f"R2: {convertirFormaPendiente(a2, b2, c2)}", color="teal")
        else:
            x_const = -c2 / a2
            plt.axvline(x_const, color='teal', label=f"R2: x = {x_const:.2f}")
    
    if resultado and resultado.get("tipo") == "interseccion" and resultado.get("punto"):
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

def calcularCoeficientesDesdePuntos(x1, y1, x2, y2):
    """Dado dos puntos, retorna los coeficientes (a, b, c) de la recta en forma Ax+By+C=0."""
    if abs(x2 - x1) < 1e-14:
        return 1, 0, -x1
    else:
        m = (y2 - y1) / (x2 - x1)
        return m, -1, y1 - m*x1

# --- Rutas de la aplicación ---

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
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Modo de entrada: "ecuacion" o "puntos"
        modo = request.form.get("modo", "ecuacion")
        solo_una = request.form.get("solo_una")  # Checkbox para graficar solo una ecuación
        rango = {}
        try:
            x_min = float(request.form.get("x_min", -10))
            x_max = float(request.form.get("x_max", 10))
            y_min = float(request.form.get("y_min", -10))
            y_max = float(request.form.get("y_max", 10))
            rango = {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}
        except ValueError:
            rango = None
        
        try:
            if modo == "ecuacion":
                a1 = float(request.form["a1"])
                b1 = float(request.form["b1"])
                c1 = float(request.form["c1"])
                if not solo_una:
                    a2 = float(request.form["a2"])
                    b2 = float(request.form["b2"])
                    c2 = float(request.form["c2"])
                else:
                    a2 = b2 = c2 = None
            elif modo == "puntos":
                x1_1 = float(request.form["x1_1"])
                y1_1 = float(request.form["y1_1"])
                x2_1 = float(request.form["x2_1"])
                y2_1 = float(request.form["y2_1"])
                a1, b1, c1 = calcularCoeficientesDesdePuntos(x1_1, y1_1, x2_1, y2_1)
                if not solo_una:
                    x1_2 = float(request.form["x1_2"])
                    y1_2 = float(request.form["y1_2"])
                    x2_2 = float(request.form["x2_2"])
                    y2_2 = float(request.form["y2_2"])
                    a2, b2, c2 = calcularCoeficientesDesdePuntos(x1_2, y1_2, x2_2, y2_2)
                else:
                    a2 = b2 = c2 = None
            else:
                return render_template("index.html", error="Modo de entrada desconocido.")
        except ValueError:
            return render_template("index.html", error="Por favor ingresa valores numéricos válidos.")
        
        if a2 is not None:
            resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
        else:
            resultado = {"tipo": "solo una recta"}
        
        datos1 = calcularDatosRecta(a1, b1, c1)
        datos2 = calcularDatosRecta(a2, b2, c2) if a2 is not None else None
        
        # Comparación de pendientes, inclinación y cálculo del ángulo entre rectas
        if datos2:
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
            
            m1 = datos1["pendiente"] if datos1["pendiente"] is not None else float('inf')
            m2 = datos2["pendiente"] if datos2["pendiente"] is not None else float('inf')
            angulo_entre = calcularAnguloEntreRectas(m1, m2)
            angulo_texto = f"🌀 Ángulo entre rectas: {angulo_entre:.2f}°"
        else:
            comp_pendiente = comp_inclinacion = angulo_texto = ""
        
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado if a2 is not None else None, rango)
        grafico = base64.b64encode(buf.getvalue()).decode("ascii")
        
        return render_template("resultado.html",
                               resultado=resultado,
                               datos1=datos1,
                               datos2=datos2,
                               comp_pendiente=comp_pendiente,
                               comp_inclinacion=comp_inclinacion,
                               angulo_texto=angulo_texto,
                               grafico=grafico)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
