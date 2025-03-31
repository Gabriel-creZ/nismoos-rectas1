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

# Configuración de sesión (para mantener el login activo)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

# ---------------------------
# Función: Convertir recta de formato general a forma pendiente-intersección
# ---------------------------
def general_to_slope_intercept(A, B, C):
    # Si B es cero, la recta es vertical y no tiene forma pendiente-intersección
    if abs(B) < 1e-8:
        return None, None  # Se puede tratar aparte
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
        # Si alguna es vertical, se considera 90° (o si ambas son verticales, 0°)
        if m1 is None and m2 is None:
            return 0.0
        return 90.0
    tan_angle = abs((m1 - m2) / (1 + m1 * m2))
    return math.degrees(math.atan(tan_angle))

# ---------------------------
# Función: Graficar las rectas con más detalles
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
        # Recta vertical, calcular constante de x
        x_const = -c1 / a1
        plt.axvline(x_const, color='darkorange', label=f"R1: x = {x_const:.2f}")
    
    y2 = get_y(a2, b2, c2, x_vals)
    if y2 is not None:
        plt.plot(x_vals, y2, label=f"R2: {a2}x + {b2}y + {c2} = 0", color="teal")
    else:
        x_const = -c2 / a2
        plt.axvline(x_const, color='teal', label=f"R2: x = {x_const:.2f}")
    
    # Graficar punto de intersección si existe
    if resultado.get("tipo") == "interseccion" and resultado.get("punto") is not None:
        x_sol, y_sol = resultado["punto"]
        plt.plot(x_sol, y_sol, 'ko', label="Intersección")
        # Calcular distancia al origen
        dist = distance_between_points(0, 0, x_sol, y_sol)
        plt.text(x_sol, y_sol, f"  ({x_sol:.2f}, {y_sol:.2f})\nDist: {dist:.2f}", fontsize=9, color="blue")
    
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
# Función: Resolver sistema de rectas usando el método de Cramer
# ---------------------------
def resolverSistema(a1, b1, c1, a2, b2, c2):
    # Reescribir en forma: a*x + b*y = -c
    A1, B1, C1 = a1, b1, -c1
    A2, B2, C2 = a2, b2, -c2
    det = A1 * B2 - A2 * B1
    resultado = {"det": det, "tipo": None, "punto": None}
    if abs(det) < 1e-8:
        # Paralelas o coincidentes: se pueden hacer más validaciones
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
    # Se espera que los resultados se guarden en la sesión
    if not session.get('logged_in') or 'export_data' not in session:
        flash("No hay datos para exportar.")
        return redirect(url_for('index'))
    
    export_data = session['export_data']  # Debe ser un diccionario con los resultados
    # Crear archivo CSV en memoria
    si = io.StringIO()
    cw = csv.writer(si)
    # Escribir encabezados
    cw.writerow(["Recta", "Pendiente", "Intersección X", "Intersección Y", "Distancia al Origen"])
    # Suponiendo que export_data tenga datos de dos rectas, ejemplo:
    # export_data = {"recta1": {...}, "recta2": {...}}
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
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            # Validación simple: usuario fijo
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
            
            # Obtener coeficientes de las dos rectas en formato general
            a1 = get_val("a1")
            b1 = get_val("b1")
            c1 = get_val("c1")
            a2 = get_val("a2")
            b2 = get_val("b2")
            c2 = get_val("c2")
            
            # Validar que se ingresaron datos
            if None in [a1, b1, c1, a2, b2, c2]:
                flash("Por favor ingresa todos los coeficientes numéricos.")
                return redirect(url_for('index'))
            
            # Resolver el sistema mediante el método de Cramer
            resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
            
            # Convertir rectas a forma pendiente-intersección (si es posible)
            m1, b_inter1 = general_to_slope_intercept(a1, b1, c1)
            m2, b_inter2 = general_to_slope_intercept(a2, b2, c2)
            
            # Calcular ángulo entre rectas
            angulo = angle_between_lines(m1, m2)
            
            # Calcular distancia del punto de intersección al origen
            if resultado.get("punto"):
                x_int, y_int = resultado["punto"]
                dist = distance_between_points(0, 0, x_int, y_int)
            else:
                dist = None
            
            # Generar gráfica con ejes, etiquetas y rango predeterminado
            grafico = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
            
            # Guardar algunos datos en sesión para exportarlos (ejemplo para dos rectas)
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
            
            # Además, se pueden enviar otros detalles: ángulo entre rectas
            datos_extra = {
                "angulo_entre_rectas": f"{angulo:.2f}°",
                "punto_interseccion": resultado.get("punto"),
                "distancia_origen": f"{dist:.2f}" if dist is not None else "N/A"
            }
            
            # Enviar todos los datos a la plantilla
            return render_template("resultado.html", 
                                   resultado=resultado, 
                                   grafico=grafico, 
                                   m1=m1, b1=b_inter1, 
                                   m2=m2, b2=b_inter2,
                                   datos_extra=datos_extra)
        except Exception as e:
            flash("Error: " + str(e))
            return redirect(url_for('index'))
    return render_template("index.html", error=None)
    
if __name__ == "__main__":
    app.run(debug=True)
