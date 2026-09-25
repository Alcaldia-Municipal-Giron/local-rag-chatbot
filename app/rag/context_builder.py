# ---------------------------------------------------------
# Construye el contexto textual que posteriormente
# será utilizado por el modelo generativo.
#
# Recibe los resultados obtenidos por el retriever
# y convierte los chunks recuperados en un único texto.
# ---------------------------------------------------------

def construir_contexto(resultados):

    fragmentos = []

    for posicion, resultado in enumerate(resultados, start=1):

        fragmento = (
            f"[Fragmento {posicion}]\n"
            f"{resultado['text']}"
        )

        fragmentos.append(fragmento)

    return "\n\n".join(fragmentos)