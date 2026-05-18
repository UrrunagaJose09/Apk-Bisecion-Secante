import flet as ft
import httpx
import asyncio
import math

# ─────────────────────────────────────────────
#  Colores
# ─────────────────────────────────────────────
BG       = "#0d1a0a"
CARD     = "#0a1208"
GREEN    = "#639922"
GREEN_LT = "#97C459"
GREEN_DK = "#3B6D11"
TEXT     = "#eaf3de"
TEXT_MUT = "#5a8a3a"
BORDER   = "#2a4a1a"
ERROR_C  = "#ef4444"


def main(page: ft.Page):
    page.title   = "Métodos Numéricos — UP"
    page.bgcolor = BG
    page.padding = 0
    page.scroll  = ft.ScrollMode.AUTO

    metodo_actual = {"valor": "biseccion"}

    # ─────────────────────────────────────────
    #  Animación: puntos pulsantes en el header
    # ─────────────────────────────────────────
    dot1 = ft.Container(width=4, height=4, bgcolor=GREEN_LT,
                        border_radius=2, opacity=1.0,
                        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT))
    dot2 = ft.Container(width=4, height=4, bgcolor=GREEN,
                        border_radius=2, opacity=0.5,
                        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT))
    dot3 = ft.Container(width=4, height=4, bgcolor=GREEN_DK,
                        border_radius=2, opacity=0.2,
                        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT))

    async def animar_dots():
        estado = 0
        while True:
            if estado == 0:
                dot1.opacity=1.0; dot2.opacity=0.4; dot3.opacity=0.1
            elif estado == 1:
                dot1.opacity=0.4; dot2.opacity=1.0; dot3.opacity=0.4
            else:
                dot1.opacity=0.1; dot2.opacity=0.4; dot3.opacity=1.0
            estado = (estado + 1) % 3
            page.update()
            await asyncio.sleep(0.8)

    # ─────────────────────────────────────────
    #  Animación: barra de progreso al calcular
    # ─────────────────────────────────────────
    barra_progreso = ft.ProgressBar(
        width=9999,
        bgcolor=BORDER,
        color=GREEN,
        visible=False,
    )

    # ─────────────────────────────────────────
    #  Status del backend animado
    # ─────────────────────────────────────────
    status_dot = ft.Container(
        width=8, height=8, bgcolor=GREEN,
        border_radius=4,
        animate_opacity=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1.0,
        tooltip="Backend activo",
    )
    status_txt = ft.Text("Backend activo", size=11, color=GREEN)

    async def pulsar_status():
        while True:
            status_dot.opacity = 0.3
            page.update()
            await asyncio.sleep(0.8)
            status_dot.opacity = 1.0
            page.update()
            await asyncio.sleep(0.8)

    # ─────────────────────────────────────────
    #  Campos
    # ─────────────────────────────────────────
    def campo(label, value, width=None):
        kw = dict(
            label=label, value=value,
            border_color=BORDER, focused_border_color=GREEN,
            label_style=ft.TextStyle(color=TEXT_MUT, size=11),
            text_style=ft.TextStyle(color=GREEN_LT, size=13),
            bgcolor=CARD, cursor_color=GREEN, border_radius=8,
        )
        if width: kw["width"] = width
        return ft.TextField(**kw)

    campo_ip      = campo("IP del backend", "127.0.0.1:8000")
    campo_funcion = campo("Función f(x)", "x**2 - 5")
    campo_a       = campo("a", "2.0", 140)
    campo_b       = campo("b", "3.0", 140)
    campo_x0      = campo("x₀", "1.0", 140)
    campo_x1      = campo("x₁", "2.0", 140)
    campo_tol     = campo("Tolerancia", "0.001", 140)
    campo_max     = campo("Máx. iter.", "50", 140)
    campo_x0.visible = False
    campo_x1.visible = False

    fila_ab  = ft.Row([campo_a, campo_b],   spacing=10)
    fila_x01 = ft.Row([campo_x0, campo_x1], spacing=10, visible=False)

    # ─────────────────────────────────────────
    #  Resultados
    # ─────────────────────────────────────────
    txt_raiz    = ft.Text("—", size=20, weight=ft.FontWeight.W_600, color=GREEN_LT)
    txt_iters   = ft.Text("—", size=20, weight=ft.FontWeight.W_600, color=GREEN_LT)
    txt_error   = ft.Text("—", size=20, weight=ft.FontWeight.W_600, color=GREEN_LT)
    txt_mensaje = ft.Text("", size=12, color="#9FE1CB", selectable=True)
    txt_status  = ft.Text("", size=12, color=ERROR_C)
    tabla_col   = ft.Column([], spacing=0)
    resultado_ref = ft.Ref[ft.Column]()

    # ─────────────────────────────────────────
    #  Tabs método
    # ─────────────────────────────────────────
    lbl_bis = ft.Text("Bisección", size=13, color=BG, weight=ft.FontWeight.W_600)
    lbl_sec = ft.Text("Secante",   size=13, color=TEXT_MUT)
    lbl_btn = ft.Text("Ejecutar método", size=14, color=BG, weight=ft.FontWeight.W_600)

    btn_bis = ft.ElevatedButton(
        content=lbl_bis, bgcolor=GREEN,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )
    btn_sec = ft.ElevatedButton(
        content=lbl_sec, bgcolor="#1a3010",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, BORDER)},
        ),
    )
    btn_calcular = ft.ElevatedButton(
        content=lbl_btn, bgcolor=GREEN,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    def cambiar_metodo(e):
        metodo_actual["valor"] = e.control.data
        es_bis = metodo_actual["valor"] == "biseccion"
        btn_bis.bgcolor = GREEN if es_bis else "#1a3010"
        lbl_bis.color   = BG if es_bis else TEXT_MUT
        btn_sec.bgcolor = GREEN if not es_bis else "#1a3010"
        lbl_sec.color   = BG if not es_bis else TEXT_MUT
        fila_ab.visible  = es_bis
        fila_x01.visible = not es_bis
        campo_x0.visible = not es_bis
        campo_x1.visible = not es_bis
        campo_funcion.value = "x**2 - 5" if es_bis else "x**3 - x - 2"
        campo_tol.value     = "0.001" if es_bis else "0.0001"
        txt_status.value = ""
        resultado_ref.current.visible = False
        page.update()

    btn_bis.data = "biseccion"; btn_bis.on_click = cambiar_metodo
    btn_sec.data = "secante";   btn_sec.on_click = cambiar_metodo

    # ─────────────────────────────────────────
    #  Tabla
    # ─────────────────────────────────────────
    def construir_tabla(iteraciones, metodo):
        tabla_col.controls.clear()
        if metodo == "biseccion":
            hdrs = ["It.", "a", "b", "c", "f(c)", "Error"]
            keys = ["iteracion","a","b","c","f_c","error"]
        else:
            hdrs = ["It.", "xₙ₋₁", "xₙ", "xₙ₊₁", "f(xₙ)", "Error"]
            keys = ["iteracion","x_n1","x_n","x_nuevo","f_x_n","error"]

        tabla_col.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(h, size=9, color=GREEN_LT,
                            weight=ft.FontWeight.W_600,
                            expand=1, text_align=ft.TextAlign.CENTER)
                    for h in hdrs
                ]),
                bgcolor=GREEN_DK, padding=8,
                border_radius=ft.BorderRadius(8,8,0,0),
            )
        )
        for i, it in enumerate(iteraciones):
            bg = CARD if i % 2 == 0 else "#0c1f09"
            vals = []
            for k in keys:
                v = it.get(k)
                if v is None: vals.append("—")
                else:
                    try: vals.append(f"{float(v):.4f}" if k!="iteracion" else str(v))
                    except: vals.append(str(v))
            tabla_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(v, size=9, color="#9FE1CB",
                                expand=1, text_align=ft.TextAlign.CENTER)
                        for v in vals
                    ]),
                    bgcolor=bg, padding=6,
                )
            )

    # ─────────────────────────────────────────
    #  Calcular
    # ─────────────────────────────────────────
    async def calcular(e):
        txt_status.value = ""
        btn_calcular.disabled = True
        lbl_btn.value = "Calculando..."
        barra_progreso.visible = True
        page.update()

        ip     = campo_ip.value.strip()
        metodo = metodo_actual["valor"]

        try:
            if metodo == "biseccion":
                payload = {
                    "funcion": campo_funcion.value.strip(),
                    "a": float(campo_a.value),
                    "b": float(campo_b.value),
                    "tolerancia": float(campo_tol.value),
                    "max_iteraciones": int(campo_max.value),
                }
                url = f"http://{ip}/biseccion"
            else:
                payload = {
                    "funcion": campo_funcion.value.strip(),
                    "x0": float(campo_x0.value),
                    "x1": float(campo_x1.value),
                    "tolerancia": float(campo_tol.value),
                    "max_iteraciones": int(campo_max.value),
                }
                url = f"http://{ip}/secante"

            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=10)

            data = r.json()
            txt_raiz.value    = str(data.get("raiz_aproximada","—"))
            txt_iters.value   = str(data.get("iteraciones_totales","—"))
            txt_error.value   = str(data.get("error_final","—"))
            txt_mensaje.value = data.get("mensaje","")
            construir_tabla(data.get("iteraciones",[]), metodo)
            resultado_ref.current.visible = True

        except ValueError:
            txt_status.value = "❌ Verifica los valores numéricos."
        except httpx.ConnectError:
            txt_status.value = f"❌ No se pudo conectar a {ip}."
            status_dot.bgcolor = ERROR_C
            status_txt.value   = "Backend inactivo"
            status_txt.color   = ERROR_C
        except Exception as ex:
            txt_status.value = f"❌ Error: {str(ex)}"

        btn_calcular.disabled = False
        lbl_btn.value = "Ejecutar método"
        barra_progreso.visible = False
        page.update()

    btn_calcular.on_click = calcular

    # ─────────────────────────────────────────
    #  Tarjeta métrica
    # ─────────────────────────────────────────
    def metrica(label, txt_ctrl):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=9, color=GREEN_DK,
                        weight=ft.FontWeight.W_600),
                txt_ctrl,
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD, border_radius=10, padding=12, expand=1,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN),
        )

    # ─────────────────────────────────────────
    #  Layout
    # ─────────────────────────────────────────
    page.add(

        # ── Header con logo ──
        ft.Container(
            content=ft.Column([
                ft.Row([
                    # Logo UP
                    ft.Container(
                        content=ft.Image(
                            src="UP-logo.png",
                            width=52, height=52,
                            fit="contain",
                            error_content=ft.Text("UP", size=16,
                                weight=ft.FontWeight.W_700, color=GREEN),
                        ),
                        border_radius=26,
                        bgcolor="white",
                        width=56, height=56,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                    ft.Column([
                        ft.Text("Métodos Numéricos", size=17,
                                weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text("Universidad de Panamá",
                                size=11, color=GREEN),
                        ft.Text("Ing. en Informática",
                                size=10, color=GREEN_DK),
                    ], spacing=1, expand=1),
                    # Status pulsante
                    ft.Column([
                        status_dot,
                        status_txt,
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=12),

                # Dots animados decorativos
                ft.Row([dot1, dot2, dot3], spacing=6),
            ], spacing=10),
            bgcolor=CARD,
            padding=ft.Padding(16,16,16,16),
            border_radius=ft.BorderRadius(0,0,16,16),
            margin=ft.Margin(0,0,0,14),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=12,
                color="#1a4a0a", offset=ft.Offset(0,4),
            ),
        ),

        # Contenido con padding
        ft.Container(
            padding=ft.Padding(16,0,16,16),
            content=ft.Column([

                # ── IP ──
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WIFI, color=GREEN, size=16),
                            ft.Text("Conexión al backend", size=11,
                                    color=TEXT_MUT, weight=ft.FontWeight.W_600),
                        ], spacing=6),
                        campo_ip,
                        ft.Text("💡 Emulador: 10.0.2.2:8000  |  WiFi: IP-local:8000",
                                size=10, color=GREEN_DK),
                    ], spacing=6),
                    bgcolor=CARD, padding=14, border_radius=12,
                    margin=ft.Margin(0,0,0,12),
                    shadow=ft.BoxShadow(blur_radius=8, color="#0a2008",
                                        offset=ft.Offset(0,2)),
                ),

                # ── Selector ──
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CALCULATE, color=GREEN, size=16),
                            ft.Text("Método numérico", size=11,
                                    color=TEXT_MUT, weight=ft.FontWeight.W_600),
                        ], spacing=6),
                        ft.Row([btn_bis, btn_sec], spacing=10),
                    ], spacing=8),
                    bgcolor=CARD, padding=14, border_radius=12,
                    margin=ft.Margin(0,0,0,12),
                    shadow=ft.BoxShadow(blur_radius=8, color="#0a2008",
                                        offset=ft.Offset(0,2)),
                ),

                # ── Formulario ──
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.FUNCTIONS, color=GREEN, size=16),
                            ft.Text("Parámetros", size=11,
                                    color=TEXT_MUT, weight=ft.FontWeight.W_600),
                        ], spacing=6),
                        campo_funcion,
                        fila_ab,
                        fila_x01,
                        ft.Row([campo_tol, campo_max], spacing=10),
                        ft.Container(height=4),
                        barra_progreso,
                        btn_calcular,
                        txt_status,
                    ], spacing=8),
                    bgcolor=CARD, padding=14, border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, color="#0a2008",
                                        offset=ft.Offset(0,2)),
                ),

                # ── Resultados ──
                ft.Column(
                    ref=resultado_ref,
                    visible=False,
                    controls=[
                        ft.Container(height=14),
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=GREEN, size=16),
                            ft.Text("Resultados", size=13, color=GREEN_LT,
                                    weight=ft.FontWeight.W_700),
                        ], spacing=6),

                        ft.Row([
                            metrica("RAÍZ",        txt_raiz),
                            metrica("ITERACIONES", txt_iters),
                            metrica("ERROR",       txt_error),
                        ], spacing=8),

                        ft.Container(
                            content=txt_mensaje,
                            bgcolor=CARD,
                            border_radius=8, padding=12,
                            margin=ft.Margin(0,4,0,4),
                            shadow=ft.BoxShadow(blur_radius=6, color="#0a2008",
                                                offset=ft.Offset(0,2)),
                        ),

                        ft.Row([
                            ft.Icon(ft.Icons.TABLE_CHART, color=GREEN, size=14),
                            ft.Text("Tabla de iteraciones", size=12,
                                    color=GREEN_LT, weight=ft.FontWeight.W_600),
                        ], spacing=6),

                        ft.Container(
                            content=tabla_col,
                            border_radius=8, bgcolor=CARD,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            shadow=ft.BoxShadow(blur_radius=8, color="#0a2008",
                                                offset=ft.Offset(0,2)),
                        ),
                    ],
                ),

                # Footer
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Félix Samudio · José Urrunaga · Jeremy Gonzalez",
                            size=10, color=GREEN_DK,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Análisis Numérico 2026",
                            size=9, color=BORDER,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    margin=ft.Margin(0,16,0,16),
                ),
            ], spacing=0),
        ),
    )

    # Iniciar animaciones
    page.run_task(animar_dots)
    page.run_task(pulsar_status)


ft.app(target=main, assets_dir="assets")
