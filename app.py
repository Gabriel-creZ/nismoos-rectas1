from flask import Flask, render_template, request, redirect, url_for, send_file
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Usar backend no interactivo
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Funciones de cálculo (refactorizadas desde tu código original)

def procedimientoCramer(a1, b1, c1, a2, b2, c2):
    texto = []
    texto.append("1) Reescribimos las ecuaciones en la forma: ")
    texto.append(f"   {a1}x + {b1}y = {-c1}")
    texto.append(f"   {a2}x + {b2}y = {-c2}")
    
    texto.append("2) Calculamos el determinante principal:")
    det = a1 * b2 - a2 * b1
    texto.append(f"   det = {a1}*{b2} - {a2}*{b1} = {det}")
    
    if abs(det) < 1e-14:
        texto.append("   Como el determinante es 0, las rectas son paralelas o coincidentes.")
    else:
        texto.append("3) Calculamos los determinantes para x e y:")
        det_x = (-c1)*b2 - (-c2)*b1
        det_y = a1*(-c2) - a2*(-c1)
        texto.append(f"   det_x = (-c1)*b2 - (-c2)*b1 = {det_x}")
        texto.append(f"   det_y = a1*(-c2) - a2*(-c1) = {det_y}")
        x_sol = det_x / det
        y_sol = det_y / det
        texto.append("4) Hallamos las soluciones:")
        texto.append(f"   x = {x_sol}")
        texto.append(f"   y = {y_sol}")
    return "<br>".join(texto)

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
    datos["distanciaAlOrigen"] = abs(c) / math.sqrt(a*a + b*b)
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
    plt.title("Gráfica de las rectas")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    # Guardamos la gráfica en un objeto BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# Rutas de la aplicación web

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Obtenemos los coeficientes del formulario
            a1 = float(request.form["a1"])
            b1 = float(request.form["b1"])
            c1 = float(request.form["c1"])
            a2 = float(request.form["a2"])
            b2 = float(request.form["b2"])
            c2 = float(request.form["c2"])
        except ValueError:
            return render_template("index.html", error="Por favor ingresa valores numéricos válidos.")
        
        # Procesamos el sistema
        proc_texto = procedimientoCramer(a1, b1, c1, a2, b2, c2)
        resultado = resolverSistema(a1, b1, c1, a2, b2, c2)
        datos1 = calcularDatosRecta(a1, b1, c1)
        datos2 = calcularDatosRecta(a2, b2, c2)
        
        # Generamos la gráfica y guardamos en sesión temporalmente
        buf = graficarRectas(a1, b1, c1, a2, b2, c2, resultado)
        # Convertimos la imagen a base64 para incrustarla en el HTML
        import base64
        grafico_base64 = base64.b64encode(buf.getvalue()).decode("ascii")
        
        return render_template("resultado.html",
                               proc_texto=proc_texto,
                               resultado=resultado,
                               datos1=datos1,
                               datos2=datos2,
                               a1=a1, b1=b1, c1=c1,
                               a2=a2, b2=b2, c2=c2,
                               grafico=grafico_base64)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
