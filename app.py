from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import math
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
import io
import base64
import csv

app = Flask(__name__)
app.secret_key = 'j350z271123r'  # Cambia esto por una clave más segura en producción

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
        return 0.0 if (m1 is None and m2 is None) else 90.0
    tan_angle = abs((m1 - m2) / (1 + m1 * m2))
    return math.degrees(math.atan(tan_angle))

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
    
    # Graficar el punto de intersección si existe
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
        # Ecuación vertical: x = -c/a
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
# Ruta para exportar resultados en CSV
# ---------------------------
@app.route('/export')
def export_results():
    if not session.get('logged_in') or 'export_data' not in session:
        flash("No hay datos para exportar.")
        return redirect(url_for('index'))
    
    export_data = session['export_data']
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Recta", "Pendiente", "Intersección X", "Intersección Y", "Distancia al Origen"])
    for key in export_data:
        data = export_data[key]
        cw.writerow([
            key,
            data.get("pendiente", "N/A"),
            data.get("interseccionX", "N/A"),
            data.get("interseccionY", "N/A"),
            data.get("distanciaAlOrigen", "N/A")
        ])
    output = si.getvalue()
    return Response(output,
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=resultados_rectas.csv"})

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

# Alias para evitar conflicto de nombres
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
            
            # Intentar obtener coeficientes para dos rectas
            a1 = get_val("a1")
            b1 = get_val("b1")
            c1 = get_val("c1")
            a2 = get_val("a2")
            b2 = get_val("b2")
            c2 = get_val("c2")
            
            # Validación: Se debe ingresar la primera recta
            if a1 is None or b1 is None or c1 is None:
                flash("Ingrese los coeficientes de al menos la primera recta.")
                return redirect(url_for('index'))
            
            modo = "dual"
            # Si la segunda recta no se ingresa, se toma modo simple
            if a2 is None and b2 is None and c2 is None:
                modo = "simple"
            
            if modo == "dual":
                resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
                m1, b_inter1 = general_to_slope_intercept(a1, b1, c1)
                m2, b_inter2 = general_to_slope_intercept(a2, b2, c2)
                angulo = angle_between_lines(m1, m2)
                if resultado.get("punto"):
                    x_int, y_int = resultado["punto"]
                    dist = distance_between_points(0, 0, x_int, y_int)
                else:
                    dist = None
                grafico = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
                
                # Guardar datos para exportar (ejemplo)
                session['export_data'] = {
                    "recta1": {
                        "pendiente": m1 if m1 is not None else "Vertical",
                        "interseccionX": (-c1 / a1) if abs(b1) < 1e-8 else "N/A",
                        "interseccionY": (-c1 / b1) if abs(b1) >= 1e-8 else "N/A",
                        "distanciaAlOrigen": dist if dist is not None else "N/A"
                    },
                    "recta2": {
                        "pendiente": m2 if m2 is not None else "Vertical",
                        "interseccionX": (-c2 / a2) if abs(b2) < 1e-8 else "N/A",
                        "interseccionY": (-c2 / b2) if abs(b2) >= 1e-8 else "N/A",
                        "distanciaAlOrigen": dist if dist is not None else "N/A"
                    }
                }
                
                datos_extra = {
                    "angulo_entre_rectas": f"{angulo:.2f}°",
                    "punto_interseccion": resultado.get("punto"),
                    "distancia_origen": f"{dist:.2f}" if dist is not None else "N/A"
                }
                
                return render_template("resultado.html", 
                                       resultado=resultado, 
                                       grafico=grafico, 
                                       datos_extra=datos_extra)
            else:
                # Modo simple: graficar una sola ecuación
                # Calcular forma pendiente-intersección
                m, b_inter = general_to_slope_intercept(a1, b1, c1)
                # Calcular intersecciones (si es posible)
                x_inter = -c1 / a1 if abs(a1) > 1e-8 else None
                y_inter = -c1 / b1 if abs(b1) > 1e-8 else None
                # Graficar la ecuación simple
                grafico = graficarEcuacionSimple(a1, b1, c1)
                # Construir un "resultado" simple para mostrar datos
                resultado = {"tipo": "simple", "pendiente": m, "interseccion": (x_inter, y_inter)}
                return render_template("resultado.html", 
                                       resultado=resultado, 
                                       grafico=grafico, 
                                       datos_extra={"modo": "simple"})
        except Exception as e:
            flash("Error: " + str(e))
            return redirect(url_for('index'))
    return render_template("index.html", error=None)

if __name__ == "__main__":
    app.run(debug=True)
