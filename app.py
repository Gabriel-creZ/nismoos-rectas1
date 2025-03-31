from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import math
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import io
import base64
import csv

app = Flask(__name__)
app.secret_key = 'j350z271123r'  # Cambia esta clave por una más segura en producción

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# ---------------------------
# Función: Convertir recta en formato general a forma pendiente-intersección
# ---------------------------
def general_to_slope_intercept(A, B, C):
    if abs(B) < 1e-8:
        return None, None  # Recta vertical
    m = -A / B
    b = -C / B
    return m, b

# ---------------------------
# Función: Calcular distancia entre dos puntos
# ---------------------------
def distance_between_points(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# ---------------------------
# Función: Calcular ángulo entre dos rectas dadas sus pendientes
# ---------------------------
def angle_between_lines(m1, m2):
    if m1 is None or m2 is None:
        # Si ambas son verticales, ángulo 0; si solo una, 90°
        if m1 is None and m2 is None:
            return 0.0
        return 90.0
    tan_angle = abs((m1 - m2) / (1 + m1 * m2))
    return math.degrees(math.atan(tan_angle))

# ---------------------------
# Función: Calcular datos detallados de una recta
# ---------------------------
def calcularDatosRecta(a, b, c):
    datos = {}
    if abs(b) < 1e-8:
        datos["pendiente"] = None
    else:
        datos["pendiente"] = -a / b
    datos["interseccionX"] = None if abs(a) < 1e-8 else -c / a
    datos["interseccionY"] = None if abs(b) < 1e-8 else -c / b
    if datos["pendiente"] is None:
        datos["anguloConEjeX"] = 90.0
    else:
        datos["anguloConEjeX"] = math.degrees(math.atan(datos["pendiente"]))
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a * a + b * b)
    return datos

# ---------------------------
# Función: Graficar dos rectas con detalles
# ---------------------------
def graficarRectas(a1, b1, c1, a2, b2, c2, resultado, x_range=(-10, 10)):
    plt.figure(figsize=(7, 7))
    x_vals = [x_range[0] + i * (x_range[1] - x_range[0]) / 400 for i in range(401)]
    
    def get_y(a, b, c, x_array):
        if abs(b) < 1e-8:
            return None  # Recta vertical
        return [(-a * x - c) / b for x in x_array]
    
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
    
    if resultado.get("tipo") == "interseccion" and resultado.get("punto"):
        x_int, y_int = resultado["punto"]
        plt.plot(x_int, y_int, 'ko', label="Intersección")
        dist = distance_between_points(0, 0, x_int, y_int)
        plt.text(x_int, y_int, f"  ({x_int:.2f}, {y_int:.2f})\nDist: {dist:.2f}", fontsize=9, color="blue")
    
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de las Rectas")
    plt.legend(loc="best")
    plt.grid(True)
    plt.xlim(x_range)
    plt.ylim(-10, 10)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close()
    return image_base64

# ---------------------------
# Función: Graficar una sola ecuación
# ---------------------------
def graficarEcuacionSimple(a, b, c, x_range=(-10, 10)):
    plt.figure(figsize=(7, 7))
    x_vals = [x_range[0] + i * (x_range[1]-x_range[0]) / 400 for i in range(401)]
    if abs(b) < 1e-8:
        x_const = -c / a
        plt.axvline(x_const, color="purple", label=f"Ecuación: x = {x_const:.2f}")
    else:
        y_vals = [(-a * x - c) / b for x in x_vals]
        plt.plot(x_vals, y_vals, color="purple", label=f"Ecuación: {a}x + {b}y + {c} = 0")
    
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de la Ecuación")
    plt.legend(loc="best")
    plt.grid(True)
    plt.xlim(x_range)
    plt.ylim(-10, 10)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close()
    return image_base64

# ---------------------------
# Función: Resolver sistema de rectas (método de Cramer)
# ---------------------------
def resolverSistema(a1, b1, c1, a2, b2, c2):
    A1, B1, C1 = a1, b1, -c1
    A2, B2, C2 = a2, b2, -c2
    det = A1 * B2 - A2 * B1
    resultado = {"det": det, "tipo": None, "punto": None}
    if abs(det) < 1e-8:
        resultado["tipo"] = "paralelas"
    else:
        x_sol = (C1 * B2 - C2 * B1) / det
        y_sol = (A1 * C2 - A2 * C1) / det
        resultado["tipo"] = "interseccion"
        resultado["punto"] = (x_sol, y_sol)
    return resultado

# ---------------------------
# Ruta para login
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            if username == 'alumno' and password == 'amrd':
                session['logged_in'] = True
                session['user'] = username
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos, intente de nuevo.')
                return render_template("login.html")
        except Exception as e:
            flash(str(e))
            return render_template("login.html")
    return render_template("login.html")

app.add_url_rule('/login', 'login', login_route, methods=['GET', 'POST'])

# ---------------------------
# Ruta para logout
# ---------------------------
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Sesión cerrada correctamente.")
    return redirect(url_for('login'))

# ---------------------------
# Ruta principal
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            def get_val(field):
                val = request.form.get(field)
                if val is None or val.strip() == "":
                    return None
                return float(val)
            
            # Primera recta: obligatoria
            a1 = get_val("a1")
            b1 = get_val("b1")
            c1 = get_val("c1")
            if a1 is None or b1 is None or c1 is None:
                flash("Ingrese los coeficientes de al menos la primera recta.")
                return redirect(url_for('index'))
            
            # Segunda recta: se considera dual solo si se llenan los 3 campos; de lo contrario, modo simple
            a2 = get_val("a2")
            b2 = get_val("b2")
            c2 = get_val("c2")
            if a2 is not None and b2 is not None and c2 is not None:
                modo = "dual"
            else:
                modo = "simple"
            
            if modo == "dual":
                resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
                datos1 = calcularDatosRecta(a1, b1, c1)
                datos2 = calcularDatosRecta(a2, b2, c2)
                m1, b_inter1 = general_to_slope_intercept(a1, b1, c1)
                m2, b_inter2 = general_to_slope_intercept(a2, b2, c2)
                angulo = angle_between_lines(m1, m2)
                if resultado.get("punto"):
                    x_int, y_int = resultado["punto"]
                    dist = distance_between_points(0, 0, x_int, y_int)
                else:
                    dist = None
                grafico = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
                
                # Comparaciones decoradas
                pendiente1 = datos1["pendiente"] if datos1["pendiente"] is not None else float('inf')
                pendiente2 = datos2["pendiente"] if datos2["pendiente"] is not None else float('inf')
                if abs(pendiente1) > abs(pendiente2):
                    comp_pendiente = f"🔥 La recta 1 tiene la mayor pendiente: {datos1['pendiente']}"
                elif abs(pendiente1) < abs(pendiente2):
                    comp_pendiente = f"🔥 La recta 2 tiene la mayor pendiente: {datos2['pendiente']}"
                else:
                    comp_pendiente = "🔥 Ambas rectas tienen la misma pendiente."
                
                if datos1["anguloConEjeX"] > datos2["anguloConEjeX"]:
                    comp_inclinacion = f"🌟 La recta 1 tiene mayor inclinación: {datos1['anguloConEjeX']}°"
                elif datos1["anguloConEjeX"] < datos2["anguloConEjeX"]:
                    comp_inclinacion = f"🌟 La recta 2 tiene mayor inclinación: {datos2['anguloConEjeX']}°"
                else:
                    comp_inclinacion = "🌟 Ambas rectas tienen la misma inclinación."
                
                return render_template("resultado.html", 
                                       resultado=resultado, 
                                       grafico=grafico, 
                                       datos1=datos1,
                                       datos2=datos2,
                                       comp_pendiente=comp_pendiente,
                                       comp_inclinacion=comp_inclinacion)
            else:
                # Modo simple: graficar una sola ecuación
                m, b_inter = general_to_slope_intercept(a1, b1, c1)
                x_inter = -c1 / a1 if abs(a1) > 1e-8 else None
                y_inter = -c1 / b1 if abs(b1) > 1e-8 else None
                grafico = graficarEcuacionSimple(a1, b1, c1)
                resultado = {"tipo": "simple", "pendiente": m, "interseccion": (x_inter, y_inter)}
                datos1 = calcularDatosRecta(a1, b1, c1)
                return render_template("resultado.html", 
                                       resultado=resultado, 
                                       grafico=grafico,
                                       datos1=datos1)
        except Exception as e:
            flash("Error: " + str(e))
            return redirect(url_for('index'))
    return render_template("index.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)
