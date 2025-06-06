from flask import Flask, render_template, request, redirect, url_for, session, flash
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'j350z271123r'  # Clave de seguridad para el login

# Configuración de sesión (para mantener el login activo)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora en segundos

# Configuración SMTP para reporte de errores
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'

# --- Funciones de cálculo y graficado ---

def resolverSistema(a1, b1, c1, a2, b2, c2):
    try:
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
    except Exception as e:
        flash(f"Error al resolver el sistema: {e}")
        return None

def calcularDatosRecta(a, b, c):
    datos = {}
    try:
        if abs(b) < 1e-14:
            datos["pendiente"] = None
        else:
            datos["pendiente"] = -a / b
        datos["interseccionX"] = None if abs(a) < 1e-14 else -c / a
        datos["interseccionY"] = None if abs(b) < 1e-14 else -c / b
        if datos["pendiente"] is None:
            datos["anguloConEjeX"] = 90.0
        else:
            datos["anguloConEjeX"] = round(math.degrees(math.atan(abs(datos["pendiente"]))), 2)
        datos["distanciaAlOrigen"] = round(abs(c) / math.sqrt(a * a + b * b), 2)
    except Exception as e:
        flash(f"Error en cálculo de la recta: {e}")
    return datos

def calcularDistancia(p1, p2):
    # p1 y p2 son tuplas (x, y)
    return round(math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2), 2)

def calcularAnguloEntreRectas(m1, m2):
    try:
        if m1 is None:  # Recta vertical
            ang1 = 90.0
        else:
            ang1 = math.degrees(math.atan(m1))
        if m2 is None:
            ang2 = 90.0
        else:
            ang2 = math.degrees(math.atan(m2))
        angulo = abs(ang1 - ang2)
        if angulo > 90:
            angulo = 180 - angulo
        return round(angulo, 2)
    except Exception as e:
        flash(f"Error al calcular ángulo entre rectas: {e}")
        return None

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
    
    if resultado and resultado["tipo"] == "interseccion" and resultado["punto"] is not None:
        x_sol, y_sol = resultado["punto"]
        plt.plot(x_sol, y_sol, 'ko', label="Intersección")
        plt.annotate(f"({round(x_sol,2)}, {round(y_sol,2)})", (x_sol, y_sol), textcoords="offset points", xytext=(5,5))
    
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

def graficarRectasInteractivo(a1, b1, c1, a2, b2, c2, resultado):
    x_vals = np.linspace(-10, 10, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    y1 = get_y(a1, b1, c1, x_vals)
    y2 = get_y(a2, b2, c2, x_vals)
    
    fig = go.Figure()
    if y1 is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y1, mode='lines', name=f"R1: {a1}x + {b1}y + {c1} = 0",
                                 line=dict(color='darkorange')))
    else:
        x_const = -c1 / a1
        fig.add_trace(go.Scatter(x=[x_const]*2, y=[-10, 10], mode='lines', name=f"R1: x = {x_const:.2f}",
                                 line=dict(color='darkorange')))
    
    if y2 is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y2, mode='lines', name=f"R2: {a2}x + {b2}y + {c2} = 0",
                                 line=dict(color='teal')))
    else:
        x_const = -c2 / a2
        fig.add_trace(go.Scatter(x=[x_const]*2, y=[-10, 10], mode='lines', name=f"R2: x = {x_const:.2f}",
                                 line=dict(color='teal')))
    
    if resultado and resultado["tipo"] == "interseccion" and resultado["punto"] is not None:
        x_sol, y_sol = resultado["punto"]
        fig.add_trace(go.Scatter(x=[x_sol], y=[y_sol], mode='markers+text',
                                 text=[f"({round(x_sol,2)}, {round(y_sol,2)})"],
                                 textposition="top center", name="Intersección", marker=dict(color='black', size=10)))
    
    fig.update_layout(title="Gráfica Interactiva de las Rectas",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      legend_title="Leyenda",
                      template="plotly_white")
    return fig.to_html(full_html=False)

def graficarUnaRecta(a, b, c):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(-10, 10, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    y = get_y(a, b, c, x_vals)
    if y is not None:
        plt.plot(x_vals, y, label=f"{a}x + {b}y + {c} = 0", color="darkorange")
    else:
        x_const = -c / a
        plt.axvline(x_const, color="darkorange", label=f"x = {x_const:.2f}")
    
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de la Recta")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

def graficarUnaRectaInteractivo(a, b, c):
    x_vals = np.linspace(-10, 10, 400)
    
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    
    y = get_y(a, b, c, x_vals)
    fig = go.Figure()
    if y is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y, mode='lines', name=f"{a}x + {b}y + {c} = 0",
                                 line=dict(color='darkorange')))
    else:
        x_const = -c / a
        fig.add_trace(go.Scatter(x=[x_const]*2, y=[-10, 10], mode='lines', name=f"x = {x_const:.2f}",
                                 line=dict(color='darkorange')))
    
    fig.update_layout(title="Gráfica Interactiva de la Recta",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      legend_title="Leyenda",
                      template="plotly_white")
    return fig.to_html(full_html=False)

def graficarTresRectas(a1, b1, c1, a2, b2, c2, a3, b3, c3, intersecciones):
    plt.figure(figsize=(7, 7))
    x_vals = np.linspace(-10, 10, 400)
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    y1 = get_y(a1, b1, c1, x_vals)
    if y1 is not None:
        plt.plot(x_vals, y1, label=f"R1: {a1}x + {b1}y + {c1} = 0", color="darkorange")
    else:
        x_const = -c1 / a1
        plt.axvline(x_const, color="darkorange", label=f"R1: x = {x_const:.2f}")
    y2 = get_y(a2, b2, c2, x_vals)
    if y2 is not None:
        plt.plot(x_vals, y2, label=f"R2: {a2}x + {b2}y + {c2} = 0", color="teal")
    else:
        x_const = -c2 / a2
        plt.axvline(x_const, color="teal", label=f"R2: x = {x_const:.2f}")
    y3 = get_y(a3, b3, c3, x_vals)
    if y3 is not None:
        plt.plot(x_vals, y3, label=f"R3: {a3}x + {b3}y + {c3} = 0", color="purple")
    else:
        x_const = -c3 / a3
        plt.axvline(x_const, color="purple", label=f"R3: x = {x_const:.2f}")
    
    # Dibujar intersecciones (si existen)
    if intersecciones.get("12") is not None:
        x_sol, y_sol = intersecciones["12"]
        plt.plot(x_sol, y_sol, "ko", label="Intersección 1-2")
        plt.annotate(f"({round(x_sol,2)}, {round(y_sol,2)})", (x_sol, y_sol), textcoords="offset points", xytext=(5,5))
    if intersecciones.get("13") is not None:
        x_sol, y_sol = intersecciones["13"]
        plt.plot(x_sol, y_sol, "ks", label="Intersección 1-3")
        plt.annotate(f"({round(x_sol,2)}, {round(y_sol,2)})", (x_sol, y_sol), textcoords="offset points", xytext=(5,5))
    if intersecciones.get("23") is not None:
        x_sol, y_sol = intersecciones["23"]
        plt.plot(x_sol, y_sol, "k^", label="Intersección 2-3")
        plt.annotate(f"({round(x_sol,2)}, {round(y_sol,2)})", (x_sol, y_sol), textcoords="offset points", xytext=(5,5))
    
    plt.axhline(0, color="black", linewidth=0.5)
    plt.axvline(0, color="black", linewidth=0.5)
    plt.xlabel("Eje X")
    plt.ylabel("Eje Y")
    plt.title("Gráfica de las Tres Rectas")
    plt.legend()
    plt.grid(True)
    plt.axis("equal")
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

def graficarTresRectasInteractivo(a1, b1, c1, a2, b2, c2, a3, b3, c3, intersecciones):
    x_vals = np.linspace(-10, 10, 400)
    def get_y(a, b, c, x_array):
        return None if abs(b) < 1e-14 else (-a * x_array - c) / b
    y1 = get_y(a1, b1, c1, x_vals)
    y2 = get_y(a2, b2, c2, x_vals)
    y3 = get_y(a3, b3, c3, x_vals)
    fig = go.Figure()
    if y1 is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y1, mode='lines', name=f"R1: {a1}x + {b1}y + {c1} = 0",
                                 line=dict(color='darkorange')))
    else:
        x_const = -c1 / a1
        fig.add_trace(go.Scatter(x=[x_const, x_const], y=[-10, 10], mode='lines', name=f"R1: x = {x_const:.2f}",
                                 line=dict(color='darkorange')))
    if y2 is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y2, mode='lines', name=f"R2: {a2}x + {b2}y + {c2} = 0",
                                 line=dict(color='teal')))
    else:
        x_const = -c2 / a2
        fig.add_trace(go.Scatter(x=[x_const, x_const], y=[-10, 10], mode='lines', name=f"R2: x = {x_const:.2f}",
                                 line=dict(color='teal')))
    if y3 is not None:
        fig.add_trace(go.Scatter(x=x_vals, y=y3, mode='lines', name=f"R3: {a3}x + {b3}y + {c3} = 0",
                                 line=dict(color='purple')))
    else:
        x_const = -c3 / a3
        fig.add_trace(go.Scatter(x=[x_const, x_const], y=[-10, 10], mode='lines', name=f"R3: x = {x_const:.2f}",
                                 line=dict(color='purple')))
    if intersecciones.get("12") is not None:
        x_sol, y_sol = intersecciones["12"]
        fig.add_trace(go.Scatter(x=[x_sol], y=[y_sol], mode='markers+text',
                                 text=[f"({round(x_sol,2)},{round(y_sol,2)})"],
                                 textposition="top center", name="Intersección 1-2",
                                 marker=dict(color='black', symbol='circle', size=10)))
    if intersecciones.get("13") is not None:
        x_sol, y_sol = intersecciones["13"]
        fig.add_trace(go.Scatter(x=[x_sol], y=[y_sol], mode='markers+text',
                                 text=[f"({round(x_sol,2)},{round(y_sol,2)})"],
                                 textposition="top center", name="Intersección 1-3",
                                 marker=dict(color='black', symbol='square', size=10)))
    if intersecciones.get("23") is not None:
        x_sol, y_sol = intersecciones["23"]
        fig.add_trace(go.Scatter(x=[x_sol], y=[y_sol], mode='markers+text',
                                 text=[f"({round(x_sol,2)},{round(y_sol,2)})"],
                                 textposition="top center", name="Intersección 2-3",
                                 marker=dict(color='black', symbol='triangle-up', size=10)))
    fig.update_layout(title="Gráfica Interactiva de las Tres Rectas",
                      xaxis_title="Eje X",
                      yaxis_title="Eje Y",
                      legend_title="Leyenda",
                      template="plotly_white")
    return fig.to_html(full_html=False)

# --- Rutas para login y autenticación ---

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

# --- Ruta principal (index) ---
@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        modo = request.form.get("modo", "dos")  # Valor por defecto: "dos"
        if modo == "una":
            try:
                a1 = float(request.form["a1"])
                b1 = float(request.form["b1"])
                c1 = float(request.form["c1"])
            except ValueError:
                return render_template("index.html", error="Por favor ingresa valores numéricos válidos.")
            
            datos1 = calcularDatosRecta(a1, b1, c1)
            buf = graficarUnaRecta(a1, b1, c1)
            grafico_estatico = base64.b64encode(buf.getvalue()).decode("ascii")
            grafico_interactivo = graficarUnaRectaInteractivo(a1, b1, c1)
            
            return render_template("resultado.html",
                                   modo="una",
                                   datos1=datos1,
                                   grafico_estatico=grafico_estatico,
                                   grafico_interactivo=grafico_interactivo)
        elif modo == "tres":
            try:
                a1 = float(request.form["a1"])
                b1 = float(request.form["b1"])
                c1 = float(request.form["c1"])
                a2 = float(request.form["a2"])
                b2 = float(request.form["b2"])
                c2 = float(request.form["c2"])
                a3 = float(request.form["a3"])
                b3 = float(request.form["b3"])
                c3 = float(request.form["c3"])
            except ValueError:
                return render_template("index.html", error="Por favor ingresa valores numéricos válidos.")
            
            datos1 = calcularDatosRecta(a1, b1, c1)
            datos2 = calcularDatosRecta(a2, b2, c2)
            datos3 = calcularDatosRecta(a3, b3, c3)
            
            inter12 = resolverSistema(a1, b1, c1, a2, b2, c2)
            inter13 = resolverSistema(a1, b1, c1, a3, b3, c3)
            inter23 = resolverSistema(a2, b2, c2, a3, b3, c3)
            intersecciones = {}
            if inter12 and inter12["tipo"] == "interseccion":
                intersecciones["12"] = inter12["punto"]
            if inter13 and inter13["tipo"] == "interseccion":
                intersecciones["13"] = inter13["punto"]
            if inter23 and inter23["tipo"] == "interseccion":
                intersecciones["23"] = inter23["punto"]
            
            grafico_interactivo = graficarTresRectasInteractivo(a1, b1, c1, a2, b2, c2, a3, b3, c3, intersecciones)
            buf = graficarTresRectas(a1, b1, c1, a2, b2, c2, a3, b3, c3, intersecciones)
            grafico_estatico = base64.b64encode(buf.getvalue()).decode("ascii")
            
            return render_template("resultado.html",
                                   modo="tres",
                                   datos1=datos1,
                                   datos2=datos2,
                                   datos3=datos3,
                                   intersecciones=intersecciones,
                                   grafico_estatico=grafico_estatico,
                                   grafico_interactivo=grafico_interactivo)
        else:  # Modo "dos"
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
            
            angulo_entre = calcularAnguloEntreRectas(datos1["pendiente"], datos2["pendiente"])
            
            distancia_interseccion = None
            if resultado and resultado["tipo"] == "interseccion" and resultado["punto"]:
                distancia_interseccion = calcularDistancia((0, 0), resultado["punto"])
            
            grafico_interactivo = graficarRectasInteractivo(a1, b1, c1, a2, b2, c2, resultado)
            buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
            grafico_estatico = base64.b64encode(buf.getvalue()).decode("ascii")
            
            return render_template("resultado.html",
                                   modo="dos",
                                   resultado=resultado,
                                   datos1=datos1,
                                   datos2=datos2,
                                   comp_pendiente=comp_pendiente,
                                   comp_inclinacion=comp_inclinacion,
                                   angulo_entre=angulo_entre,
                                   distancia_interseccion=distancia_interseccion,
                                   grafico_estatico=grafico_estatico,
                                   grafico_interactivo=grafico_interactivo)
    return render_template("index.html")

# --- Rutas adicionales ---
@app.route("/donar")
def donar():
    return render_template("donar.html")

@app.route("/reporte", methods=["GET", "POST"])
def reporte():
    if request.method == "POST":
        email = request.form.get("email")
        mensaje = request.form.get("mensaje")
        asunto = "Reporte de error desde Instant Math Solver"
        cuerpo = f"Reporte de: {email}\n\nMensaje:\n{mensaje}"
        msg = MIMEText(cuerpo)
        msg['Subject'] = asunto
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER  # O a otro correo receptor

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            flash("Reporte enviado correctamente. ¡Gracias por tus comentarios!")
        except Exception as e:
            flash(f"Error al enviar el reporte: {e}")
        return redirect(url_for("reporte"))
    return render_template("reporte.html")

if __name__ == "__main__":
    app.run(debug=True)